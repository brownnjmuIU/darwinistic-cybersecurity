"""
Provider-agnostic reasoning helper.

Each agent can optionally ask an LLM to phrase its reasoning. If no API key /
provider is configured, every agent falls back to deterministic rule-based
logic, so the whole system runs on Render with zero setup and zero cost. You
can wire in a real model later by setting the env vars below; nothing else
changes.

    LLM_PROVIDER_MODEL   e.g. "openai/gpt-oss-120b"
    OPENAI_API_KEY       your model provider / REALLMS key
    OPENAI_API_BASE      (optional) a custom endpoint, e.g. IU REALLMS

We route through litellm if it is installed so any OpenAI-compatible model
works. If litellm is absent or the call fails, we silently use the fallback.
"""

from __future__ import annotations

import os

# Fold smart punctuation to plain ASCII so model text renders cleanly in the
# dashboard and in raw JSON, regardless of how a browser guesses the charset.
_PUNCT = {
    "’": "'", "‘": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-",
    "…": "...",
}


def _clean(text: str) -> str:
    for bad, good in _PUNCT.items():
        text = text.replace(bad, good)
    return text


def llm_enabled() -> bool:
    return bool(os.getenv("LLM_PROVIDER_MODEL") and os.getenv("OPENAI_API_KEY"))


def active_backend() -> str:
    """Human-readable name of the reasoning backend currently configured."""
    return "IU REALLMS model" if llm_enabled() else "built-in logic"


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
        return _clean(resp["choices"][0]["message"]["content"].strip())
    except Exception:
        # Any failure (no package, bad key, rate limit) -> deterministic path.
        return fallback
