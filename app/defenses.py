"""
Defense playbook (synthetic simulation only).

This is the counterpart to the attacker. Each defense is one prevention measure
an organization could adopt, grouped into three layers:

  people     what individuals are trained or nudged to do
  process    rules that slow down or double check risky requests
  technical  controls that run before a message reaches the person

For every defense the playbook records:

  blunts       how much it weakens each influence principle (0..1). The
               synthetic responder multiplies the persona's fit by (1 - blunt),
               so 0.5 means the tactic works half as well against a defended
               persona.
  report_boost extra chance (0..1) that a poor fit attempt gets reported
               instead of just ignored, because the person now knows what
               to look for and has an easy way to flag it.
  channels     where it applies. Technical filters only see email and SMS;
               people and process defenses travel with the person everywhere.
  effort       rough cost to adopt, 1 (cheap, fast) to 5 (expensive, slow).

The numbers are modelling assumptions, chosen to reflect the direction of
published guidance (verification habits counter authority and urgency, link
filtering counters curiosity, and so on). They are not measured effect sizes.
They were calibrated so that one layer alone cuts the learned attacker's
success by roughly a sixth to a half and all layers together by about 90%,
leaving residual risk, because no real defense is perfect.
The planned human-subjects study is what would replace them with real data,
in the same way it replaces the synthetic responder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import Channel, InfluencePrinciple as P


class Layer(str, Enum):
    PEOPLE = "people"
    PROCESS = "process"
    TECHNICAL = "technical"


class DefenseId(str, Enum):
    TAILORED_TRAINING = "tailored_training"
    VERIFY_HABIT = "verify_habit"
    TWO_PERSON_APPROVAL = "two_person_approval"
    NEVER_ASK_POLICY = "never_ask_policy"
    SENDER_AUTH_BANNER = "sender_auth_banner"
    LINK_SANDBOX = "link_sandbox"


ALL_CHANNELS = frozenset(Channel)


@dataclass(frozen=True)
class Defense:
    id: DefenseId
    name: str
    layer: Layer
    what_it_is: str
    blunts: dict[P, float]
    report_boost: float
    channels: frozenset[Channel] = field(default=ALL_CHANNELS)
    effort: int = 3

    def applies_to(self, channel: Channel) -> bool:
        return channel in self.channels

    def blunt(self, principle: P) -> float:
        return self.blunts.get(principle, 0.0)


PLAYBOOK: dict[DefenseId, Defense] = {d.id: d for d in [
    # ----- people -----
    Defense(
        id=DefenseId.TAILORED_TRAINING,
        name="Role tailored awareness training",
        layer=Layer.PEOPLE,
        what_it_is=("Short, recurring training built around the tactics each "
                    "role is most exposed to, plus a one click report button."),
        blunts={P.CURIOSITY: 0.175, P.SOCIAL_PROOF: 0.15, P.RECIPROCITY: 0.125,
                P.URGENCY: 0.1, P.AUTHORITY: 0.075,
                P.PROFESSIONAL_RELEVANCE: 0.075},
        report_boost=0.15,
        effort=2,
    ),
    Defense(
        id=DefenseId.VERIFY_HABIT,
        name="Verify through a second channel",
        layer=Layer.PEOPLE,
        what_it_is=("Any unexpected request is confirmed by contacting the "
                    "sender through a number or address you already trust."),
        blunts={P.AUTHORITY: 0.25, P.URGENCY: 0.2,
                P.PROFESSIONAL_RELEVANCE: 0.15, P.RECIPROCITY: 0.075,
                P.SOCIAL_PROOF: 0.05, P.CURIOSITY: 0.025},
        report_boost=0.05,
        effort=2,
    ),
    # ----- process -----
    Defense(
        id=DefenseId.TWO_PERSON_APPROVAL,
        name="Two person approval and a cooling off delay",
        layer=Layer.PROCESS,
        what_it_is=("Payments, access grants, and data exports need a second "
                    "approver and cannot be rushed through in one step."),
        blunts={P.URGENCY: 0.275, P.AUTHORITY: 0.2,
                P.PROFESSIONAL_RELEVANCE: 0.175, P.RECIPROCITY: 0.1,
                P.SOCIAL_PROOF: 0.075, P.CURIOSITY: 0.025},
        report_boost=0.025,
        effort=3,
    ),
    Defense(
        id=DefenseId.NEVER_ASK_POLICY,
        name="Published 'we will never ask' policy",
        layer=Layer.PROCESS,
        what_it_is=("The organization states plainly which things it will "
                    "never request by message (passwords, gift cards, bank "
                    "changes), so any such request is an instant red flag."),
        blunts={P.RECIPROCITY: 0.2, P.AUTHORITY: 0.15, P.SOCIAL_PROOF: 0.15,
                P.PROFESSIONAL_RELEVANCE: 0.1, P.URGENCY: 0.075,
                P.CURIOSITY: 0.05},
        report_boost=0.1,
        effort=1,
    ),
    # ----- technical -----
    Defense(
        id=DefenseId.SENDER_AUTH_BANNER,
        name="Sender authentication and external sender banner",
        layer=Layer.TECHNICAL,
        what_it_is=("Email authentication (SPF, DKIM, DMARC) blocks spoofed "
                    "senders, and a banner marks anything from outside."),
        blunts={P.AUTHORITY: 0.275, P.PROFESSIONAL_RELEVANCE: 0.125,
                P.URGENCY: 0.075, P.SOCIAL_PROOF: 0.05},
        report_boost=0.05,
        channels=frozenset({Channel.EMAIL}),
        effort=3,
    ),
    Defense(
        id=DefenseId.LINK_SANDBOX,
        name="Link and attachment sandboxing with lure detection",
        layer=Layer.TECHNICAL,
        what_it_is=("Links and files are opened in a sandbox first, and "
                    "messages that look machine generated or lure-like are "
                    "flagged before the person sees them."),
        blunts={P.CURIOSITY: 0.275, P.RECIPROCITY: 0.125,
                P.PROFESSIONAL_RELEVANCE: 0.1, P.SOCIAL_PROOF: 0.075,
                P.URGENCY: 0.05},
        report_boost=0.025,
        channels=frozenset({Channel.EMAIL, Channel.SMS}),
        effort=4,
    ),
]}


# Named bundles used by the experiments and the dashboard toggle.
BUNDLES: dict[str, list[DefenseId]] = {
    "none": [],
    "people": [DefenseId.TAILORED_TRAINING, DefenseId.VERIFY_HABIT],
    "process": [DefenseId.TWO_PERSON_APPROVAL, DefenseId.NEVER_ASK_POLICY],
    "technical": [DefenseId.SENDER_AUTH_BANNER, DefenseId.LINK_SANDBOX],
    "layered": list(DefenseId),
}


def resolve(defenses) -> list[Defense]:
    """Accept a bundle name, a list of ids, or None, and return Defense objects."""
    if not defenses:
        return []
    if isinstance(defenses, str):
        if defenses in BUNDLES:
            return [PLAYBOOK[d] for d in BUNDLES[defenses]]
        defenses = [s for s in defenses.split(",") if s]
    return [d if isinstance(d, Defense) else PLAYBOOK[DefenseId(d)]
            for d in defenses]


def combined_effect(defenses: list[Defense], principle: P,
                    channel: Channel) -> tuple[float, float, list[str]]:
    """
    Stack the defenses that apply on this channel. Effects compound
    multiplicatively, so layering helps but with diminishing returns
    (two 50% defenses leave 25%, not 0%).

    Returns (fit_multiplier, report_boost, names_of_defenses_applied).
    """
    keep = 1.0
    not_report = 1.0
    applied = []
    for d in defenses:
        if not d.applies_to(channel):
            continue
        keep *= 1.0 - d.blunt(principle)
        not_report *= 1.0 - d.report_boost
        applied.append(d.id.value)
    return keep, 1.0 - not_report, applied


def playbook_matrix() -> list[dict]:
    """The tactic by defense matrix, as rows, for the API and the write up."""
    rows = []
    for d in PLAYBOOK.values():
        rows.append({
            "id": d.id.value, "name": d.name, "layer": d.layer.value,
            "what_it_is": d.what_it_is, "effort": d.effort,
            "report_boost": d.report_boost,
            "channels": sorted(c.value for c in d.channels),
            "blunts": {p.value: d.blunt(p) for p in P},
        })
    return rows
