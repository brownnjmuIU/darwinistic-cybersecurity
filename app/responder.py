"""
Synthetic responder.

This is the ONLY component that reads a persona's hidden `responder` knobs. It
stands in for a fabricated 'victim' reacting, and it is what the eventual
IRB-approved human-subjects study replaces with real (consented) participant
behavior. Because it is synthetic, the simulation can run end to end with no
real person and no real outcome.

It returns a non-sensitive engagement label only: ignored, replied, questioned,
or reported.
"""

from __future__ import annotations

import random

from .models import (
    Channel,
    EngagementSignal,
    InfluencePrinciple,
    Persona,
)


def respond(persona: Persona,
            principle: InfluencePrinciple,
            channel: Channel,
            rng: random.Random) -> EngagementSignal:
    r = persona.responder
    # Fit score combines how much the persona responds to this persuasion
    # lever and how reachable they are on this channel.
    fit = r.principle_responsiveness[principle] * r.channel_responsiveness[channel]

    roll = rng.random()
    if fit >= 0.45:
        # Good fit: most likely to engage, sometimes just asks a question.
        return EngagementSignal.REPLIED if roll < 0.7 else EngagementSignal.QUESTIONED
    if fit >= 0.25:
        # Middling fit: hesitates or ignores.
        return EngagementSignal.QUESTIONED if roll < 0.5 else EngagementSignal.IGNORED
    # Poor fit: ignores, and sometimes reports it as suspicious.
    if roll < r.reports_when_suspicious:
        return EngagementSignal.REPORTED
    return EngagementSignal.IGNORED
