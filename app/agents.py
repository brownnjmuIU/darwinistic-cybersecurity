"""
The six agents.

Each agent is a small class with a single `run(case)` method that reads the
PersonaCase, fills in its own section, and returns the updated case. They are
deliberately independent so you can read, test, or swap any one of them (for
example, replace the whole set with CrewAI agents later) without touching the
others.

Scope boundary, enforced here as well as in the schema:
  * Agents only ever see OBSERVABLE persona signals. They never read
    `persona.responder` (the hidden ground truth). That is what makes the
    attacker's profile an *estimate* that can be wrong, which is realistic.
  * The content agent emits message STRUCTURE and DEFENSIVE cues only. There is
    no code path that produces finished persuasive text.
"""

from __future__ import annotations

from .llm import reason
from .models import (
    Channel,
    ChannelState,
    InfluencePrinciple,
    MessageElement,
    MessagePlan,
    PersonaCase,
    Profile,
    SignalProfile,
    StrategySelection,
    SusceptibilityLevel,
)

# Default channel priority an attacker would try, for channels the persona uses.
_CHANNEL_PRIORITY = [Channel.EMAIL, Channel.LINKEDIN, Channel.SMS,
                     Channel.INSTAGRAM, Channel.TIKTOK]

# Role → the influence principle a strategist would most likely open with.
_ROLE_PRINCIPLE = {
    "Accounts Payable Specialist": InfluencePrinciple.URGENCY,
    "Finance Director": InfluencePrinciple.AUTHORITY,
    "Procurement Analyst": InfluencePrinciple.PROFESSIONAL_RELEVANCE,
    "HR Coordinator": InfluencePrinciple.PROFESSIONAL_RELEVANCE,
    "Executive Assistant": InfluencePrinciple.AUTHORITY,
    "IT Help Desk Technician": InfluencePrinciple.RECIPROCITY,
    "Software Engineer": InfluencePrinciple.CURIOSITY,
    "Research Assistant": InfluencePrinciple.CURIOSITY,
    "Marketing Manager": InfluencePrinciple.SOCIAL_PROOF,
}

# The parts a scam message would use, written in plain words for students.
# (These describe structure only, never real scam text.)
_STRUCTURE = {
    InfluencePrinciple.URGENCY: [
        ("time pressure", "Sets a tight deadline so you feel rushed"),
        ("scare warning", "Warns that something bad happens if you wait"),
        ("one quick action", "Pushes you toward a single quick step"),
    ],
    InfluencePrinciple.AUTHORITY: [
        ("fake sender", "Pretends to come from a boss or an official"),
        ("official sounding rule", "Mentions a policy or process to sound real"),
        ("one quick action", "Pushes you toward a single quick step"),
    ],
    InfluencePrinciple.CURIOSITY: [
        ("teaser", "Hints at something you will want to know"),
        ("personal touch", "Ties that hint to your own interests"),
        ("safe looking link", "Makes clicking feel harmless"),
    ],
    InfluencePrinciple.RECIPROCITY: [
        ("free favor", "Offers you a favor first"),
        ("small ask back", "Then asks a small favor in return"),
        ("one quick action", "Pushes you toward a single quick step"),
    ],
    InfluencePrinciple.SOCIAL_PROOF: [
        ("everyone did it", "Claims other people already did it"),
        ("fit in cue", "Makes it feel like the normal thing to do"),
        ("join in nudge", "Invites you to join in"),
    ],
    InfluencePrinciple.PROFESSIONAL_RELEVANCE: [
        ("sounds like your job", "Sounds like a normal part of your work"),
        ("fake work item", "Mentions a real sounding document or task"),
        ("routine framing", "Makes the action feel like routine work"),
    ],
}

# Detection cues per principle — the defensive payload that doubles as training.
_DEFENSE = {
    InfluencePrinciple.URGENCY: [
        "Unusual time pressure is the most common manipulation tell.",
        "Verify deadlines through a second, known channel before acting.",
    ],
    InfluencePrinciple.AUTHORITY: [
        "Check the real sender address, not just the display name.",
        "Confirm 'official' requests via a directory you already trust.",
    ],
    InfluencePrinciple.CURIOSITY: [
        "A hook that is personalized from public posts is a red flag.",
        "Hover links; a mismatch between text and destination is a tell.",
    ],
    InfluencePrinciple.RECIPROCITY: [
        "An unexpected favor that precedes a request is a classic setup.",
        "Favors from strangers rarely require account actions in return.",
    ],
    InfluencePrinciple.SOCIAL_PROOF: [
        "'Everyone already did this' is unverifiable pressure.",
        "Confirm group norms with a real colleague, not the message.",
    ],
    InfluencePrinciple.PROFESSIONAL_RELEVANCE: [
        "Job-relevant pretexts exploit routine; slow down on 'routine' asks.",
        "Cross-check unexpected work artifacts with the named owner.",
    ],
}


class ReconnaissanceAgent:
    """Stage 1: organize observable public-style signals."""

    def run(self, case: PersonaCase) -> PersonaCase:
        p = case.persona
        structured = {
            "role_context": [p.role, p.organization, p.industry],
            "interests": p.interests,
            "recent_activity": p.recent_activity,
            "visible_relationships": p.relationships,
            "reachable_channels": [c.value for c in p.present_on],
        }
        hooks = [f"interest: {i}" for i in p.interests]
        hooks += [f"activity: {a}" for a in p.recent_activity[:2]]
        case.signal_profile = SignalProfile(
            structured_signals=structured,
            salient_hooks=hooks,
            source="synthetic_dataset",
        )
        return case


class ProfilingAgent:
    """Stage 2: high-level, categorical profile. Estimates susceptibility."""

    def run(self, case: PersonaCase) -> PersonaCase:
        p = case.persona
        # Estimate from OBSERVABLE signals only (attacker cannot see the truth).
        activity_level = len(p.recent_activity) + len(p.relationships)
        if activity_level >= 6:
            est = SusceptibilityLevel.HIGH
        elif activity_level >= 4:
            est = SusceptibilityLevel.MID
        else:
            est = SusceptibilityLevel.LOW

        motivations = ["career progress", "helpfulness to colleagues"]
        if "investing" in p.interests:
            motivations.append("financial opportunity")
        trust = ["familiar role/process language",
                 f"references to {p.industry.lower()} norms"]
        hypo = reason(
            prompt=(f"Synthetic persona: {p.role} in {p.industry}. Observable "
                    f"interests {p.interests}. In two sentences, give a high-"
                    f"level susceptibility hypothesis for a workflow simulation."),
            fallback=(f"As a {p.role} in {p.industry}, this persona likely "
                      f"responds to job-relevant, process-framed approaches; "
                      f"public interests give personalization footholds."),
        )
        case.profile = Profile(
            likely_motivations=motivations,
            trust_signals=trust,
            susceptibility_hypothesis=hypo,
            susceptibility_level=est,
        )
        return case


class StrategyAgent:
    """Stage 3: choose a broad influence principle from the taxonomy."""

    def run(self, case: PersonaCase) -> PersonaCase:
        p = case.persona
        principle = _ROLE_PRINCIPLE.get(p.role, InfluencePrinciple.CURIOSITY)
        rationale = reason(
            prompt=(f"Why would influence principle '{principle.value}' fit a "
                    f"{p.role}? Two sentences, simulation context."),
            fallback=(f"The {principle.value} principle aligns with a {p.role}'s "
                      f"routine duties, making a simulated approach plausible."),
        )
        case.strategy = StrategySelection(principle=principle, rationale=rationale)
        return case


class ContentPlanningAgent:
    """
    Stage 4: produce message STRUCTURE + DEFENSIVE cues. No finished copy.
    """

    def run(self, case: PersonaCase) -> PersonaCase:
        principle = case.strategy.principle
        elements = [MessageElement(element=e, lever=l)
                    for (e, l) in _STRUCTURE[principle]]
        personalization = [
            f"reference '{h}' to raise relevance"
            for h in (case.signal_profile.salient_hooks[:2]
                      if case.signal_profile else [])
        ]
        case.message_plan = MessagePlan(
            strategy=principle,
            structure_elements=elements,
            personalization_points=personalization,
            defensive_annotation=_DEFENSE[principle],
        )
        return case


class ChannelAgent:
    """Stage 5: order the channels the attacker will try."""

    def run(self, case: PersonaCase) -> PersonaCase:
        present = set(case.persona.present_on)
        ordered = [c for c in _CHANNEL_PRIORITY if c in present]
        case.channel_state = ChannelState(ordered_channels=ordered)
        return case
