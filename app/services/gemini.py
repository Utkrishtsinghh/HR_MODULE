import json
import re
from typing import Any

from app.core.config import settings

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None


def _fallback_tags(jd_text: str) -> list[dict[str, Any]]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{2,}", jd_text)
    unique = []
    for w in words:
        lw = w.lower()
        if lw not in unique:
            unique.append(lw)
        if len(unique) >= 15:
            break
    return [{"tag": w, "weight": 0.5} for w in unique]


def generate_tags(jd_text: str) -> list[dict[str, Any]]:
    if not settings.gemini_api_key or not genai:
        return _fallback_tags(jd_text)

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "Extract 20 ATS tags with relevance scores (0-1) from this JD. "
        "Return JSON array with keys tag and weight only.\n\n"
        f"JD:\n{jd_text}"
    )
    response = model.generate_content(prompt)
    text = response.text or ""

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

    return _fallback_tags(jd_text)
