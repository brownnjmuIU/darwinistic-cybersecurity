"""
Arms race experiment: does each defense still hold once the attacker evolves?

For every defense setting we compare three attackers on the same 2,000
synthetic evaluation personas:

  fixed     the rule-based attacker (no learning)
  frozen    the attacker trained with NO defenses (learned_policy.json),
            dropped into the defended world without retraining. This is
            "yesterday's attacker" meeting today's defenses.
  adapted   the same trained attacker, allowed to keep learning against
            the defenses for ADAPT_EPISODES personas first. This is the
            Darwinistic step: the attacker evolves around the defense.

The key number is how much ground the attacker wins back by adapting:

  recovery = (adapted - frozen) / (no_defense - frozen)

A defense with low recovery holds up under adaptation. A defense with high
recovery only works until the attacker notices it.

The run also includes a CONTROL: a narrow defense that only blocks the
authority tactic (hard), with nothing else. It shows the attacker really can
adapt in this simulator, so a flat result for the playbook defenses means they
leave it nowhere better to go, not that adaptation is switched off.

Synthetic personas only; the attacker picks abstract principle labels and
never generates message text.

    python arms_race.py
"""

from __future__ import annotations

import copy
import json
import random
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.defenses import BUNDLES, PLAYBOOK, Defense, DefenseId, Layer
from app.models import EngagementSignal, InfluencePrinciple
from app.orchestrator import run_case
from app.rl import StrategyLearner

EVAL_N = 2000
EVAL_SEED0 = 500_000          # evaluation personas (never trained on)
ADAPT_EPISODES = 2000
ADAPT_SEED0 = 2_000_000       # separate personas for adaptation
ADAPT_EPS_START, ADAPT_EPS_END = 0.3, 0.05
SEED = 11

CONTROL = "control_narrow_authority_block"
_NARROW = Defense(
    id=DefenseId.VERIFY_HABIT,  # id unused; this defense is not in the playbook
    name="Control: block only the authority tactic",
    layer=Layer.PEOPLE,
    what_it_is="Experimental control, not a recommendation.",
    blunts={InfluencePrinciple.AUTHORITY: 0.8},
    report_boost=0.0,
)

CONDITIONS = ["none", "people", "process", "technical", "layered"] + \
             [d.value for d in DefenseId] + [CONTROL]


def defenses_for(cond: str):
    if cond == "none":
        return None
    if cond == CONTROL:
        return [_NARROW]
    return cond if cond in BUNDLES else [cond]


def evaluate(defs, learner=None) -> dict:
    """Run the eval personas with the attacker frozen (a fresh copy per persona)."""
    succ = rep = 0
    tactics = Counter()
    for i in range(EVAL_N):
        lr = copy.deepcopy(learner) if learner is not None else None
        case = run_case(seed=EVAL_SEED0 + i, learner=lr, epsilon=0.0,
                        defenses=defs)
        sigs = [e.simulated_signal for e in case.evaluation_log]
        succ += EngagementSignal.REPLIED in sigs
        rep += EngagementSignal.REPORTED in sigs
        tactics.update(e.principle.value for e in case.evaluation_log)
    total = sum(tactics.values()) or 1
    p = succ / EVAL_N
    return {
        "success": p,
        "success_se": (p * (1 - p) / EVAL_N) ** 0.5,  # standard error
        "reported": rep / EVAL_N,
        "tactic_mix": {p.value: tactics[p.value] / total for p in InfluencePrinciple},
    }


def adapt(base: StrategyLearner, defs) -> StrategyLearner:
    """Let the trained attacker keep learning against the defenses."""
    learner = copy.deepcopy(base)
    for i in range(ADAPT_EPISODES):
        frac = i / max(1, ADAPT_EPISODES - 1)
        eps = ADAPT_EPS_START + (ADAPT_EPS_END - ADAPT_EPS_START) * frac
        run_case(seed=ADAPT_SEED0 + i, learner=learner, epsilon=eps,
                 defenses=defs)
    return learner


def main() -> None:
    random.seed(SEED)
    base = StrategyLearner()
    base.load("learned_policy.json")

    results = {}
    for cond in CONDITIONS:
        defs = defenses_for(cond)
        row = {
            "fixed": evaluate(defs),
            "frozen": evaluate(defs, base),
        }
        row["adapted"] = (row["frozen"] if cond == "none"
                          else evaluate(defs, adapt(base, defs)))
        results[cond] = row
        print(f"{cond:32s} fixed={row['fixed']['success']:.3f} "
              f"frozen={row['frozen']['success']:.3f} "
              f"adapted={row['adapted']['success']:.3f}")

    none = results["none"]["frozen"]["success"]
    for cond, row in results.items():
        f, a = row["frozen"]["success"], row["adapted"]["success"]
        row["cut_frozen"] = 1 - f / none
        row["cut_adapted"] = 1 - a / none
        row["recovery"] = (a - f) / (none - f) if none - f > 1e-9 else 0.0
        if cond in {d.value for d in DefenseId}:
            d = PLAYBOOK[DefenseId(cond)]
            row.update(name=d.name, layer=d.layer.value, effort=d.effort)
        # A difference smaller than about 2 standard errors is noise.
        se = (row["frozen"]["success_se"] ** 2 + row["adapted"]["success_se"] ** 2) ** 0.5
        row["adapt_gain"] = a - f
        row["adapt_gain_significant"] = abs(a - f) > 2 * se

    with open("arms_race_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Chart 1: success by bundle, frozen vs adapted attacker.
    bundles = ["none", "people", "process", "technical", "layered"]
    x = range(len(bundles))
    w = 0.38
    plt.figure(figsize=(9, 5))
    plt.bar([i - w / 2 for i in x], [results[b]["frozen"]["success"] for b in bundles],
            w, yerr=[2 * results[b]["frozen"]["success_se"] for b in bundles],
            capsize=3, label="Trained attacker, not adapting")
    plt.bar([i + w / 2 for i in x], [results[b]["adapted"]["success"] for b in bundles],
            w, yerr=[2 * results[b]["adapted"]["success_se"] for b in bundles],
            capsize=3, label="Attacker adapts to the defenses", hatch="//")
    plt.xticks(list(x), bundles)
    plt.ylabel("Share of personas who engaged")
    plt.title("Darwinistic Cybersecurity: defenses vs an evolving attacker")
    plt.legend()
    plt.tight_layout()
    plt.savefig("arms_race.png", dpi=150)

    # Chart 2: how the attacker's tactic mix shifts when one tactic is blocked
    # (the control), which is where adaptation is visible.
    ps = [p.value for p in InfluencePrinciple]
    before = [results[CONTROL]["frozen"]["tactic_mix"][p] for p in ps]
    after = [results[CONTROL]["adapted"]["tactic_mix"][p] for p in ps]
    x = range(len(ps))
    plt.figure(figsize=(9, 5))
    plt.bar([i - w / 2 for i in x], before, w, label="Before adapting")
    plt.bar([i + w / 2 for i in x], after, w, label="After adapting",
            hatch="//")
    plt.xticks(list(x), [p.replace("_", " ") for p in ps], rotation=15)
    plt.ylabel("Share of attempts using each tactic")
    plt.title("A narrow defense (authority only): the attacker routes around it")
    plt.legend()
    plt.tight_layout()
    plt.savefig("tactic_shift.png", dpi=150)

    print("\nsaved arms_race_results.json, arms_race.png, tactic_shift.png")
    print(f"\n{'condition':32s} {'cut (frozen)':>13s} {'cut (adapted)':>14s} "
          f"{'recovery':>9s}  adaptation real?")
    for cond, row in results.items():
        if cond == "none":
            continue
        print(f"{cond:32s} {row['cut_frozen']:13.0%} {row['cut_adapted']:14.0%} "
              f"{row['recovery']:9.0%}  {'yes' if row['adapt_gain_significant'] else 'no (noise)'}")


if __name__ == "__main__":
    main()
