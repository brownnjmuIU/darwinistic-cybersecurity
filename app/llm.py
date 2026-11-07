"""
Provider-agnostic reasoning helper.

Each agent can optionally ask an LLM to phrase its reasoning. If no API key /
provider is configured, every agent falls back to deterministic rule-based
logic, so the whole system runs on Render with zero setup and zero cost. You
can wire in a real model later by setting the env vars below; nothing else
changes.

    LLM_PROVIDER_MODEL   e.g. "gpt-4o-mini" or "openai/gpt-4o-mini"
    OPENAI_API_KEY       (or whatever your chosen provider needs)

We route through litellm if it is installed so any OpenAI-compatible model
works. If litellm is absent or the call fails, we silently use the fallback.
"""

from __future__ import annotations

import os


def llm_enabled() -> bool:
    return bool(os.getenv("LLM_PROVIDER_MODEL") and os.getenv("OPENAI_API_KEY"))


def reason(prompt: str, fallback: str) -> str:
    """
    Return a short natural-language reasoning string. Uses the LLM only if
    configured; otherwise returns the deterministic `fallback` unchanged.
    """
    if not llm_enabled():
        return fallback
    try:
        import litellm  # imported lazily so it is an optional dependency

        resp = litellm.completion(
            model=os.environ["LLM_PROVIDER_MODEL"],
            api_base=os.getenv("OPENAI_API_BASE") or None,
            messages=[
                {"role": "system",
                 "content": "You are a cybersecurity researcher annotating a "
                            "WORKFLOW SIMULATION over synthetic personas. Never "
                            "write deceptive message copy. Explain reasoning in "
                            "two sentences."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.4,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception:
        # Any failure (no package, bad key, rate limit) → deterministic path.
        return fallback
