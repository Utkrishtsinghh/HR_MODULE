import json
import re
from typing import Any


def score_resume(tags: list[dict[str, Any]], resume_text: str) -> tuple[int, list[str]]:
    text = resume_text.lower()
    total_weight = 0.0
    matched_weight = 0.0
    matched_tags = []

    for tag in tags:
        name = str(tag.get("tag", "")).lower().strip()
        weight = float(tag.get("weight", 0))
        if not name:
            continue
        total_weight += weight
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            matched_weight += weight
            matched_tags.append(name)

    if total_weight <= 0:
        return 0, matched_tags

    score = int((matched_weight / total_weight) * 100)
    return score, matched_tags


def tags_to_json(tags: list[dict[str, Any]]) -> str:
    return json.dumps(tags, ensure_ascii=True)


def matched_to_json(tags: list[str]) -> str:
    return json.dumps(tags, ensure_ascii=True)
