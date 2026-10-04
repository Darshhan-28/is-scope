"""Optional LLM layer (extraction / terminology normalization ONLY).

If no API key is configured this module is never required to produce output:
the deterministic extractor in extraction.py is always the fallback and the
final standard recommendation NEVER comes from an LLM (see applicability.py).
"""
import os

SUPPORTED_PROVIDERS = ("openai_compatible", "gemini")


def llm_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY"))


def normalize_with_llm(spec_text: str) -> dict | None:
    """Attempt LLM terminology normalization; return None on any failure.

    The caller must treat None as 'use deterministic path'. Even on success,
    the returned dict only carries attribute hints — standard IDs from an
    LLM are rejected downstream.
    """
    try:
        # Stub: wire a real provider here. Deliberately returns None so the
        # prototype is fully reproducible offline.
        if not llm_configured():
            return None
        return None
    except Exception:
        return None
