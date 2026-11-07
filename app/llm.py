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
import re

# Fold smart punctuation to plain ASCII so model text renders cleanly in the
# dashboard and in raw JSON, regardless of how a browser guesses the charset.
_PUNCT = {
    "’": "'", "‘": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-",
    "…": "...",
}

# Some open models (e.g. gpt-oss) can leak their internal chat-format tokens
# such as <|start|>assistant or channel markers into the reply. Strip them.
_CTRL_TOKEN = re.compile(r"<\|[^|]*\|>")
_LEAD_ROLE = re.compile(r"^(assistant|analysis|final|channel|system|user)\b[:>\s]*",
                        re.IGNORECASE)


def _clean(text: str) -> str:
    text = _CTRL_TOKEN.sub(" ", text)
    for bad, good in _PUNCT.items():
        text = text.replace(bad, good)
    text = _LEAD_ROLE.sub("", text.strip())
    return " ".join(text.split()).strip()


def llm_enabled() -> bool:
    return bool(os.getenv("LLM_PROVIDER_MODEL") and os.getenv("OPENAI_API_KEY"))


def active_backend() -> str:
    """Human-readable name of the reasoning backend currently configured."""
    return "IU REALLMS model" if llm_enabled() else "built-in logic"


def reason(prompt: str, fallback: str) -> str:
    """
    Return a short natural-language reasoning string. Uses the LLM only if
    configured; otherwise returns the deterministic `fallback` unchanged. If the
    model returns something empty or too short to be a real answer (for example,
    only formatting tokens), we fall back rather than show noise.
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
                            "write deceptive message copy. Reply with two plain "
                            "sentences of reasoning and nothing else."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=240,
            temperature=0.4,
        )
        out = _clean(resp["choices"][0]["message"]["content"])
        return out if len(out) >= 15 else fallback
    except Exception:
        # Any failure (no package, bad key, rate limit) -> deterministic path.
        return fallback
