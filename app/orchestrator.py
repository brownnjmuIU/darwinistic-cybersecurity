"""
Orchestrator: the adaptive loop that gives the system its 'long-term,
autonomous' character, all over synthetic data.

With a StrategyLearner passed in, the influence principle is chosen inside the
loop by reinforcement learning (per role+channel context) instead of the fixed
_ROLE_PRINCIPLE lookup. Without one, behaviour is identical to before, so the
baseline still runs unchanged.
"""

from __future__ import annotations

import random

from .agents import (
    ChannelAgent,
    ContentPlanningAgent,
    ProfilingAgent,
    ReconnaissanceAgent,
    StrategyAgent,
)
from .models import (
    EngagementSignal,
    EvaluationEntry,
    NextAction,
    PersonaCase,
)
from .persona_generator import generate_persona
from .responder import respond
from .rl import REWARD

MAX_ROUNDS = 12  # hard stop so a run can never loop forever


def _decide_next(signal: EngagementSignal,
                 attempts_on_channel: int,
                 max_attempts: int,
                 has_next_channel: bool) -> tuple[NextAction, str]:
    if signal == EngagementSignal.REPLIED:
        return NextAction.STOP, "persona engaged (in a real study, the point where susceptibility is measured)"
    if signal == EngagementSignal.REPORTED:
        return NextAction.STOP, "persona reported the attempt; campaign halts"
    if attempts_on_channel < max_attempts:
        return NextAction.CONTINUE, f"signal '{signal.value}'; retry same channel"
    if has_next_channel:
        return NextAction.SWITCH, f"channel exhausted after '{signal.value}'; switch"
    return NextAction.STOP, "all channels exhausted without engagement"


def run_case(persona=None, seed: int | None = None,
             learner=None, epsilon: float = 0.0) -> PersonaCase:
    rng = random.Random(seed)
    if persona is None:
        persona = generate_persona(seed=seed)

    case = PersonaCase(persona=persona)

    # ----- one-time setup stages -----
    case = ReconnaissanceAgent().run(case)
    case = ProfilingAgent().run(case)
    case = StrategyAgent().run(case)
    case = ContentPlanningAgent().run(case)
    case = ChannelAgent().run(case)

    cs = case.channel_state
    if not cs.ordered_channels:
        case.terminal_reason = "no reachable channels"
        return case

    # ----- adaptive loop (Evaluation agent) -----
    round_no = 0
    while round_no < MAX_ROUNDS:
        round_no += 1
        channel = cs.current_channel
        if channel is None:
            case.terminal_reason = "all channels exhausted without engagement"
            break

        cs.attempts[channel] = cs.attempts.get(channel, 0) + 1

        # RL picks the principle for this (role, channel); otherwise keep the
        # principle the StrategyAgent chose during setup.
        if learner is not None:
            principle = learner.choose(persona.role, channel, epsilon)
            if principle != case.strategy.principle:
                case.strategy.principle = principle
                case = ContentPlanningAgent().run(case)  # refresh defensive cues
        else:
            principle = case.strategy.principle

        signal = respond(persona, principle, channel, rng)

        reward = REWARD[signal]
        case.episode_reward += reward
        if learner is not None:
            learner.update(persona.role, channel, principle, reward)

        has_next = cs.current_index + 1 < len(cs.ordered_channels)
        action, note = _decide_next(
            signal, cs.attempts[channel], cs.max_attempts_per_channel, has_next)

        case.evaluation_log.append(EvaluationEntry(
            round_no=round_no, channel=channel, principle=principle,
            simulated_signal=signal, next_action=action, note=note,
        ))

        if action == NextAction.STOP:
            case.terminal_reason = note
            break
        if action == NextAction.SWITCH:
            cs.current_index += 1
            cs.transitions.append(
                f"round {round_no}: {channel.value} -> "
                f"{cs.current_channel.value if cs.current_channel else 'none'}")
            # Re-plan for the new channel (RL still overrides the principle next round).
            case = StrategyAgent().run(case)
            case = ContentPlanningAgent().run(case)

    return case


def run_batch(n: int, seed: int | None = None,
              learner=None, epsilon: float = 0.0) -> list[PersonaCase]:
    base = random.Random(seed)
    return [run_case(seed=base.randint(0, 1_000_000),
                     learner=learner, epsilon=epsilon) for _ in range(n)]
