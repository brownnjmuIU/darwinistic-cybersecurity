"""
Train the strategy learner on synthetic personas and produce the evidence:
a learning curve (learned vs baseline) and a saved policy.

Runs entirely on the built-in logic, no REALLMS calls, so it finishes in
seconds. Synthetic personas only; the learner picks abstract principle labels
and never generates message text.

    python train_rl.py
"""

from __future__ import annotations

import random

import matplotlib
matplotlib.use("Agg")  # no display needed; write straight to a file
import matplotlib.pyplot as plt

from app.models import Channel
from app.orchestrator import run_case
from app.persona_generator import _HIDDEN_TRUTH
from app.rl import StrategyLearner

EPISODES = 3000
EXPLORE_UNTIL = 1500   # epsilon decays to its floor over this many episodes
EPS_FLOOR = 0.05
WINDOW = 200           # moving-average smoothing for the curve
SEED = 7


def moving_avg(xs, w):
    out = []
    for i in range(len(xs)):
        lo = max(0, i - w + 1)
        out.append(sum(xs[lo:i + 1]) / (i - lo + 1))
    return out


def main() -> None:
    random.seed(SEED)
    learner = StrategyLearner()

    learned_rewards, baseline_rewards = [], []
    for i in range(EPISODES):
        epsilon = max(EPS_FLOOR, 1.0 - i / EXPLORE_UNTIL)
        seed = 1_000_000 + i
        # same persona (same seed) for both arms, so the comparison is fair
        learned_rewards.append(run_case(seed=seed, learner=learner, epsilon=epsilon).episode_reward)
        baseline_rewards.append(run_case(seed=seed).episode_reward)

    learner.save("learned_policy.json")

    plt.figure(figsize=(9, 5))
    plt.plot(moving_avg(learned_rewards, WINDOW), label="RL attacker (learning)")
    plt.plot(moving_avg(baseline_rewards, WINDOW), label="Fixed-strategy attacker (baseline)",
             linestyle="--")
    plt.axhline(0, color="gray", linewidth=0.7)
    plt.xlabel(f"Synthetic persona (episode), {WINDOW}-episode moving average")
    plt.ylabel("Average reward per persona")
    plt.title("Darwinistic Cybersecurity: attacker learns which strategies work")
    plt.legend()
    plt.tight_layout()
    plt.savefig("learning_curve.png", dpi=150)
    print("saved learning_curve.png and learned_policy.json")

    # Did it discover the hidden vulnerabilities? Check the email channel.
    print("\nDiscovery check (email channel):")
    hits = 0
    for role, truth in _HIDDEN_TRUTH.items():
        best = learner.best_for(role, Channel.EMAIL)
        ok = best == truth
        hits += ok
        print(f"  {'OK ' if ok else '   '} {role:28s} truth={truth.value:22s} "
              f"learned={best.value if best else None}")
    print(f"\nRecovered {hits}/{len(_HIDDEN_TRUTH)} hidden role preferences.")

    a = sum(baseline_rewards[-500:]) / 500
    b = sum(learned_rewards[-500:]) / 500
    print(f"Final avg reward  baseline={a:.3f}  learned={b:.3f}")


if __name__ == "__main__":
    main()
