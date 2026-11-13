"""
Reinforcement learning for strategy selection (synthetic simulation only).

A contextual bandit: the attacker learns, per (role, channel) context, which
influence principle earns the best simulated reaction. It never generates
message text; it only picks among the abstract principle labels already in
models.py. All feedback comes from the synthetic responder.
"""

from __future__ import annotations

import json
import random

from .models import EngagementSignal, InfluencePrinciple

PRINCIPLES = list(InfluencePrinciple)

# Reward per simulated reaction. Getting reported is the worst outcome for an
# attacker, so it is the strongest negative; a question is partial engagement.
REWARD = {
    EngagementSignal.REPLIED: 1.0,
    EngagementSignal.QUESTIONED: 0.3,
    EngagementSignal.IGNORED: 0.0,
    EngagementSignal.REPORTED: -1.0,
}


class StrategyLearner:
    """Tracks the running average reward of each principle in each context."""

    def __init__(self) -> None:
        self.Q: dict[str, dict[InfluencePrinciple, float]] = {}
        self.N: dict[str, dict[InfluencePrinciple, int]] = {}

    @staticmethod
    def _key(role: str, channel) -> str:
        return f"{role}|{channel.value}"

    def choose(self, role: str, channel, epsilon: float = 0.0) -> InfluencePrinciple:
        """Epsilon-greedy: explore at random with prob epsilon, else exploit."""
        k = self._key(role, channel)
        if k not in self.Q or random.random() < epsilon:
            return random.choice(PRINCIPLES)
        return max(PRINCIPLES, key=lambda p: self.Q[k].get(p, 0.0))

    def update(self, role: str, channel, principle: InfluencePrinciple,
               reward: float) -> None:
        """Incremental average: Q += (reward - Q) / N."""
        k = self._key(role, channel)
        self.Q.setdefault(k, {})
        self.N.setdefault(k, {})
        self.N[k][principle] = self.N[k].get(principle, 0) + 1
        q = self.Q[k].get(principle, 0.0)
        self.Q[k][principle] = q + (reward - q) / self.N[k][principle]

    def best_for(self, role: str, channel) -> InfluencePrinciple | None:
        k = self._key(role, channel)
        if k not in self.Q:
            return None
        return max(PRINCIPLES, key=lambda p: self.Q[k].get(p, 0.0))

    def save(self, path: str) -> None:
        data = {k: {p.value: v for p, v in d.items()} for k, d in self.Q.items()}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        with open(path) as f:
            raw = json.load(f)
        self.Q = {k: {InfluencePrinciple(p): v for p, v in d.items()}
                  for k, d in raw.items()}
        self.N = {k: {InfluencePrinciple(p): 1 for p in d} for k, d in raw.items()}
