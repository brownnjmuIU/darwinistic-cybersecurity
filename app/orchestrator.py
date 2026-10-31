"""
Orchestrator: the adaptive loop that gives the system its 'long-term,
autonomous' character — all over synthetic data.

Flow:
  1. Run the one-time setup agents (recon → profiling → strategy → content →
     channel ordering).
  2. Then loop: on the current channel, the synthetic responder emits an
     engagement signal; the Evaluation agent logs it and decides the next
     action (continue, switch channel, or stop). Switching channels re-runs the
     strategy and content agents so the approach adapts, exactly the
     omnichannel escalation Nick's table describes.

The orchestrator chooses each next action itself, which is the 'autonomy' the
brief asks for, bounded to the simulation.
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

MAX_ROUNDS = 12  # hard stop so a run can never loop forever


def _decide_next(signal: EngagementSignal,
                 attempts_on_channel: int,
                 max_attempts: int,
                 has_next_channel: bool) -> tuple[NextAction, str]:
    if signal == EngagementSignal.REPLIED:
        return NextAction.STOP, "persona engaged (in a real study, the point where susceptibility is measured)"
    if signal == EngagementSignal.REPORTED:
        return NextAction.STOP, "persona reported the attempt; campaign halts"
    # IGNORED or QUESTIONED → keep trying this channel, then switch.
    if attempts_on_channel < max_attempts:
        return NextAction.CONTINUE, f"signal '{signal.value}'; retry same channel"
    if has_next_channel:
        return NextAction.SWITCH, f"channel exhausted after '{signal.value}'; switch"
    return NextAction.STOP, "all channels exhausted without engagement"


def run_case(persona=None, seed: int | None = None) -> PersonaCase:
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
        principle = case.strategy.principle
        signal = respond(persona, principle, channel, rng)

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
            # Adapt: re-select strategy + content for the new channel.
            case = StrategyAgent().run(case)
            case = ContentPlanningAgent().run(case)

    return case


def run_batch(n: int, seed: int | None = None) -> list[PersonaCase]:
    base = random.Random(seed)
    return [run_case(seed=base.randint(0, 1_000_000)) for _ in range(n)]
