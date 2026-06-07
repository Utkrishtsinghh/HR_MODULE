"""
ATS tag generation with multi-provider fallback.

Priority order:
  1. Gemini  (gemini-2.5-flash)
  2. OpenAI  (gpt-4o-mini)   – if Gemini fails or output looks hallucinated
  3. Claude  (claude-haiku-4-5) – if OpenAI also fails
  4. _fallback_tags()         – pure regex, zero AI

Hallucination heuristic
-----------------------
A response is flagged as hallucinated when:
  • Fewer than 5 tags are returned  (model gave up / truncated)
  • More than 40% of tags are NOT substring-matched inside the JD text
    (model invented keywords that don't appear in the source document)
"""

import json
import re
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── optional imports ──────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
except Exception:          # pragma: no cover
    genai = None

try:
    from openai import OpenAI as _OpenAI
except Exception:          # pragma: no cover
    _OpenAI = None

try:
    import anthropic as _anthropic
except Exception:          # pragma: no cover
    _anthropic = None


# ── constants ─────────────────────────────────────────────────────────────────
_MIN_TAGS = 5
_MAX_HALLUCINATION_RATIO = 0.40   # tolerate up to 40 % "invented" tags

_PROMPT = (
    "Extract exactly 20 ATS (Applicant Tracking System) keyword tags with "
    "relevance scores from the job description below. "
    "Return ONLY a valid JSON array where every element has exactly two keys: "
    '"tag" (string, lowercase) and "weight" (float between 0 and 1). '
    "No markdown, no code fences, no extra text.\n\nJD:\n{jd}"
)


# ── helpers ───────────────────────────────────────────────────────────────────
def _fallback_tags(jd_text: str) -> list[dict[str, Any]]:
    """Pure-regex fallback — no AI required."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{2,}", jd_text)
    seen: list[str] = []
    for w in words:
        lw = w.lower()
        if lw not in seen:
            seen.append(lw)
        if len(seen) >= 15:
            break
    return [{"tag": w, "weight": 0.5} for w in seen]


def _parse_tags(raw: str) -> list[dict[str, Any]] | None:
    """
    Try to extract a JSON list of {tag, weight} dicts from *raw*.
    Returns None if parsing fails entirely.
    """
    raw = raw.strip()
    # strip ```json … ``` fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```$", "", raw).strip()

    # attempt direct parse
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # attempt to grab the first [...] block
    match = re.search(r"\[[\s\S]*?]", raw)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    return None


def _is_hallucinated(tags: list[dict[str, Any]], jd_text: str) -> bool:
    """
    Returns True when the tag list looks hallucinated:
      - Too few tags (model bailed out)
      - Too many tags not found anywhere in the JD
    """
    if len(tags) < _MIN_TAGS:
        logger.warning("Hallucination check: only %d tags returned (min %d)", len(tags), _MIN_TAGS)
        return True

    jd_lower = jd_text.lower()
    invented = sum(
        1 for t in tags
        if str(t.get("tag", "")).lower().strip() not in jd_lower
    )
    ratio = invented / len(tags)
    if ratio > _MAX_HALLUCINATION_RATIO:
        logger.warning(
            "Hallucination check: %.0f%% of tags not found in JD (threshold %.0f%%)",
            ratio * 100,
            _MAX_HALLUCINATION_RATIO * 100,
        )
        return True

    return False


# ── provider implementations ──────────────────────────────────────────────────
def _try_gemini(jd_text: str) -> list[dict[str, Any]] | None:
    if not settings.gemini_api_key or not genai:
        logger.debug("Gemini skipped: no key or library missing")
        return None
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(_PROMPT.format(jd=jd_text))
        tags = _parse_tags(response.text or "")
        if tags is None:
            logger.warning("Gemini: could not parse JSON response")
            return None
        if _is_hallucinated(tags, jd_text):
            logger.warning("Gemini: hallucination detected — trying backup")
            return None
        logger.info("Gemini: returned %d tags", len(tags))
        return tags
    except Exception as exc:
        logger.warning("Gemini error: %s", exc)
        return None


def _try_openai(jd_text: str) -> list[dict[str, Any]] | None:
    if not settings.openai_api_key or not _OpenAI:
        logger.debug("OpenAI skipped: no key or library missing")
        return None
    try:
        client = _OpenAI(api_key=settings.openai_api_key)
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an ATS keyword extraction assistant. Always reply with raw JSON only.",
                },
                {"role": "user", "content": _PROMPT.format(jd=jd_text)},
            ],
            temperature=0.2,
        )
        raw = chat.choices[0].message.content or ""
        tags = _parse_tags(raw)
        if tags is None:
            logger.warning("OpenAI: could not parse JSON response")
            return None
        if _is_hallucinated(tags, jd_text):
            logger.warning("OpenAI: hallucination detected — trying next backup")
            return None
        logger.info("OpenAI: returned %d tags", len(tags))
        return tags
    except Exception as exc:
        logger.warning("OpenAI error: %s", exc)
        return None


def _try_claude(jd_text: str) -> list[dict[str, Any]] | None:
    if not settings.claude_api_key or not _anthropic:
        logger.debug("Claude skipped: no key or library missing")
        return None
    try:
        client = _anthropic.Anthropic(api_key=settings.claude_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system="You are an ATS keyword extraction assistant. Always reply with raw JSON only.",
            messages=[{"role": "user", "content": _PROMPT.format(jd=jd_text)}],
        )
        raw = message.content[0].text if message.content else ""
        tags = _parse_tags(raw)
        if tags is None:
            logger.warning("Claude: could not parse JSON response")
            return None
        if _is_hallucinated(tags, jd_text):
            logger.warning("Claude: hallucination detected — falling back to regex")
            return None
        logger.info("Claude: returned %d tags", len(tags))
        return tags
    except Exception as exc:
        logger.warning("Claude error: %s", exc)
        return None


# ── public entry point ────────────────────────────────────────────────────────
def generate_tags(jd_text: str) -> list[dict[str, Any]]:
    """
    Try Gemini → OpenAI → Claude → regex fallback.
    Always returns a non-empty list of {tag, weight} dicts.
    """
    for provider in (_try_gemini, _try_openai, _try_claude):
        result = provider(jd_text)
        if result:
            return result

    logger.warning("All AI providers failed — using regex fallback")
    return _fallback_tags(jd_text)