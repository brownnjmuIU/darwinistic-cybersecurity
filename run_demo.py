"""
Run the simulation from the command line, no server needed.

    python run_demo.py            # 3 personas
    python run_demo.py 5 42       # 5 personas, seed 42
"""

import json
import sys

from app.orchestrator import run_batch


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    cases = run_batch(n, seed=seed)
    for c in cases:
        p = c.persona
        print("=" * 72)
        print(f"{p.display_name} | {p.role} | {p.industry}")
        print(f"  attacker's estimate : {c.profile.susceptibility_level.value}")
        print(f"  (hidden truth)      : {p.responder.base_susceptibility.value}")
        print(f"  opening strategy    : {c.strategy.principle.value}")
        print(f"  channels tried      : {[e.channel.value for e in c.evaluation_log]}")
        print(f"  signals             : {[e.simulated_signal.value for e in c.evaluation_log]}")
        print(f"  outcome             : {c.terminal_reason}")
        print(f"  defensive cues      : {c.message_plan.defensive_annotation[0]}")
    print("=" * 72)
    print(f"{n} synthetic personas simulated. No real data, no message copy generated.")


if __name__ == "__main__":
    main()
