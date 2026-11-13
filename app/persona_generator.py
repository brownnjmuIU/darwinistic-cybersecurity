"""
Synthetic persona generator.

Produces entirely fabricated personas (Faker-backed) with the hidden
ResponderModel knobs the evaluation loop needs. No real data, no scraping.

Later, for the IRB-approved deployed study, a `from_consented_participant(...)`
constructor can build the same Persona object from inputs a participant
voluntarily supplies. The rest of the pipeline would not change, which is the
point of routing everything through this one module.
"""

from __future__ import annotations

import random
import uuid

from faker import Faker

from .models import (
    Channel,
    InfluencePrinciple,
    Persona,
    ResponderModel,
    SusceptibilityLevel,
)

fake = Faker()

_ROLES = [
    "Accounts Payable Specialist", "HR Coordinator", "Software Engineer",
    "Marketing Manager", "Finance Director", "Research Assistant",
    "IT Help Desk Technician", "Procurement Analyst", "Executive Assistant",
]

# Hidden ground truth: each role's TRUE most-exploitable principle.
# Deliberately different from the attacker's _ROLE_PRINCIPLE guesses in
# agents.py, so the RL agent must discover these through trial and error.
_HIDDEN_TRUTH = {
    "Accounts Payable Specialist": InfluencePrinciple.AUTHORITY,
    "Finance Director": InfluencePrinciple.URGENCY,
    "Procurement Analyst": InfluencePrinciple.SOCIAL_PROOF,
    "HR Coordinator": InfluencePrinciple.CURIOSITY,
    "Executive Assistant": InfluencePrinciple.RECIPROCITY,
    "IT Help Desk Technician": InfluencePrinciple.PROFESSIONAL_RELEVANCE,
    "Software Engineer": InfluencePrinciple.AUTHORITY,
    "Research Assistant": InfluencePrinciple.SOCIAL_PROOF,
    "Marketing Manager": InfluencePrinciple.URGENCY,
}
_INDUSTRIES = ["Higher Education", "Healthcare", "Fintech", "Manufacturing",
               "Retail", "Public Sector", "SaaS"]
_INTERESTS = ["marathon running", "home cooking", "open-source", "travel",
              "photography", "youth soccer coaching", "investing", "gardening",
              "machine learning", "true-crime podcasts", "cycling", "gaming"]
_ACTIVITY_TEMPLATES = [
    "posted about a recent {topic} milestone",
    "shared an article on {topic}",
    "celebrated a work anniversary",
    "commented on a colleague's promotion",
    "asked a public question about {topic}",
    "reposted a conference announcement",
]


def _susceptibility() -> SusceptibilityLevel:
    return random.choices(
        list(SusceptibilityLevel),
        weights=[0.4, 0.4, 0.2],  # fewer high-susceptibility personas
    )[0]


def _responder(level: SusceptibilityLevel) -> ResponderModel:
    # Higher base susceptibility nudges every principle's responsiveness up.
    base = {"low": 0.25, "mid": 0.5, "high": 0.75}[level.value]

    def jitter() -> float:
        return round(min(1.0, max(0.0, random.gauss(base, 0.15))), 2)

    return ResponderModel(
        base_susceptibility=level,
        principle_responsiveness={p: jitter() for p in InfluencePrinciple},
        channel_responsiveness={c: round(random.uniform(0.2, 0.9), 2)
                                for c in Channel},
        reports_when_suspicious=round(
            {"low": 0.5, "mid": 0.3, "high": 0.15}[level.value]
            + random.uniform(-0.05, 0.05), 2),
    )


def generate_persona(seed: int | None = None) -> Persona:
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    level = _susceptibility()
    interests = random.sample(_INTERESTS, k=random.randint(2, 4))
    activity = [
        t.format(topic=random.choice(interests))
        for t in random.sample(_ACTIVITY_TEMPLATES, k=3)
    ]
    channels = random.sample(list(Channel), k=random.randint(3, 5))

    role = random.choice(_ROLES)
    responder = _responder(level)

    # Boost the role's hidden true principle so there is a real, learnable
    # pattern for the RL agent to find (synthetic personas only).
    truth = _HIDDEN_TRUTH.get(role)
    if truth is not None:
        responder.principle_responsiveness[truth] = min(
            1.0, responder.principle_responsiveness[truth] + 0.3)

    return Persona(
        persona_id=str(uuid.uuid4())[:8],
        display_name=fake.name(),
        role=role,
        organization=fake.company(),
        industry=random.choice(_INDUSTRIES),
        interests=interests,
        recent_activity=activity,
        relationships=[f"{fake.name()} ({random.choice(_ROLES)})"
                       for _ in range(random.randint(2, 3))],
        present_on=channels,
        responder=responder,
    )


def from_public_profile(code, role, organization, industry,
                        interests, recent_activity, relationships,
                        present_on) -> Persona:
    """Build a Persona from a small sample of real, PUBLIC profile data
    (job category + a few skills only; no names, no contact info).
    The responder knobs are a synthetic placeholder and are NOT used: the
    real-data test runs only recon/profiling/strategy, never the attack
    loop, so no real person is attacked or contacted."""
    channels = [Channel(c) for c in present_on]
    return Persona(
        persona_id=code, display_name=code, role=role,
        organization=organization, industry=industry, interests=interests,
        recent_activity=recent_activity, relationships=relationships,
        present_on=channels, responder=_responder(SusceptibilityLevel.MID),
    )


def generate_batch(n: int, seed: int | None = None) -> list[Persona]:
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
    return [generate_persona() for _ in range(n)]
