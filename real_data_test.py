"""Real-data input test (Nov 14): run a small sample of real, public,
pseudonymized profiles through recon -> profiling -> strategy and print the
personalized strategy and a defense tip for each. Outcomes stay synthetic;
no attack loop, no message text, no contact."""
import json
from app.persona_generator import from_public_profile
from app.agents import (ReconnaissanceAgent, ProfilingAgent,
                        StrategyAgent, ContentPlanningAgent)
from app.models import PersonaCase

profiles = json.load(open("real_profiles.json"))
print(f"Loaded {len(profiles)} real (pseudonymized) profiles.\n")
for d in profiles:
    case = PersonaCase(persona=from_public_profile(**d))
    for agent in (ReconnaissanceAgent(), ProfilingAgent(),
                  StrategyAgent(), ContentPlanningAgent()):
        case = agent.run(case)
    p = case.persona
    print("="*64)
    print(f"{p.persona_id} | {p.role} | {p.industry}")
    print(f"  signals the system read : {p.recent_activity}")
    print(f"  planned strategy        : {case.strategy.principle.value}")
    print(f"  defense tip             : {case.message_plan.defensive_annotation[0]}")
print("="*64)
print("Real footprint in, personalized strategy + defense tip out. "
      "No message text, no contact, outcomes remain synthetic.")
