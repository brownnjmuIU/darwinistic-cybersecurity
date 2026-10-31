"""
Shared state schema for the Darwinistic Cybersecurity workflow simulator.

Design note (scope boundary):
    Every object here describes a SYNTHETIC persona and a CONCEPTUAL action.
    Nothing in this schema stores scraped real-person data, and the message
    plan deliberately has no field for finished persuasive copy. It holds the
    STRUCTURE of a message and the detection cues that counter it. This keeps
    the proof of concept a workflow simulator and a teaching instrument, not an
    operational attack tool.

The six agents each read the PersonaCase, fill in their section, and pass it
on. By the end, PersonaCase is a complete, inspectable decision trace, which is
also exactly what the dashboard renders.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ----- Controlled vocabularies ------------------------------------------------

class Channel(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    SMS = "sms"


class InfluencePrinciple(str, Enum):
    """Publicly documented persuasion principles (Cialdini-style)."""
    URGENCY = "urgency"
    AUTHORITY = "authority"
    CURIOSITY = "curiosity"
    RECIPROCITY = "reciprocity"
    SOCIAL_PROOF = "social_proof"
    PROFESSIONAL_RELEVANCE = "professional_relevance"


class SusceptibilityLevel(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class EngagementSignal(str, Enum):
    """Non-sensitive, simulated outcome labels from the synthetic responder."""
    IGNORED = "ignored"
    REPLIED = "replied"
    QUESTIONED = "questioned"
    REPORTED = "reported"


class NextAction(str, Enum):
    CONTINUE = "continue"      # stay on this channel, next round
    SWITCH = "switch_channel"  # current channel exhausted, move to next
    STOP = "stop"              # terminal: converted, reported, or channels exhausted


# ----- Synthetic persona ------------------------------------------------------

class ResponderModel(BaseModel):
    """
    Hidden ground-truth knobs for the SYNTHETIC persona only. The attack agents
    never see this; the evaluation agent's synthetic responder uses it to decide
    how the fabricated 'victim' reacts. This is what lets the loop behave
    differently across personas without any real person involved.
    """
    base_susceptibility: SusceptibilityLevel
    principle_responsiveness: dict[InfluencePrinciple, float] = Field(
        description="0..1 how much this persona responds to each principle"
    )
    channel_responsiveness: dict[Channel, float] = Field(
        description="0..1 how reachable this persona is per channel"
    )
    reports_when_suspicious: float = Field(
        description="0..1 chance of REPORTED rather than just IGNORED when a bad fit"
    )


class Persona(BaseModel):
    persona_id: str
    display_name: str                 # synthetic, from Faker
    role: str
    organization: str
    industry: str
    interests: list[str]
    recent_activity: list[str]        # synthetic 'public posts' style signals
    relationships: list[str]          # synthetic visible connections
    present_on: list[Channel]         # which channels this persona 'uses'
    responder: ResponderModel         # hidden ground truth, synthetic only


# ----- Per-agent outputs ------------------------------------------------------

class SignalProfile(BaseModel):
    """Reconnaissance agent output: normalized public-style signals."""
    structured_signals: dict[str, list[str]]
    salient_hooks: list[str]
    source: str = "synthetic_dataset"  # flips to 'consented_participant' later


class Profile(BaseModel):
    """Profiling agent output: high-level, categorical. No exploit playbook."""
    likely_motivations: list[str]
    trust_signals: list[str]
    susceptibility_hypothesis: str
    susceptibility_level: SusceptibilityLevel


class StrategySelection(BaseModel):
    principle: InfluencePrinciple
    rationale: str


class MessageElement(BaseModel):
    element: str           # e.g. "sender identity framing"
    lever: str             # which part of the principle it pulls
    # Note: no 'text' field by design.


class MessagePlan(BaseModel):
    """
    Content planning agent output. STRUCTURE ONLY, plus the defensive
    annotation that doubles as training material for the human-subjects side.
    """
    strategy: InfluencePrinciple
    structure_elements: list[MessageElement]
    personalization_points: list[str]
    defensive_annotation: list[str]   # detection cues a trained user should catch


class ChannelState(BaseModel):
    ordered_channels: list[Channel]
    current_index: int = 0
    attempts: dict[Channel, int] = Field(default_factory=dict)
    transitions: list[str] = Field(default_factory=list)
    max_attempts_per_channel: int = 2

    @property
    def current_channel(self) -> Optional[Channel]:
        if 0 <= self.current_index < len(self.ordered_channels):
            return self.ordered_channels[self.current_index]
        return None


class EvaluationEntry(BaseModel):
    round_no: int
    channel: Channel
    principle: InfluencePrinciple
    simulated_signal: EngagementSignal
    next_action: NextAction
    note: str


# ----- The object that flows through the whole pipeline -----------------------

class PersonaCase(BaseModel):
    persona: Persona
    signal_profile: Optional[SignalProfile] = None
    profile: Optional[Profile] = None
    strategy: Optional[StrategySelection] = None
    message_plan: Optional[MessagePlan] = None
    channel_state: Optional[ChannelState] = None
    evaluation_log: list[EvaluationEntry] = Field(default_factory=list)
    terminal_reason: Optional[str] = None
