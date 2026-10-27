"""
Priority and sentiment analysis (transparent, rule-based).

Priority  : High / Medium / Low from urgency phrases, number of negative
            signals and a per-category minimum (e.g. fraud is never Low).
Sentiment : lexicon score in [-1, 1] with simple negation handling.
"""

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils import config  # noqa: E402


def _contains(text_low: str, term: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", text_low) is not None


def analyze_sentiment(text: str) -> dict:
    words = re.findall(r"[a-z']+", (text or "").lower())
    if not words:
        return {"label": "Neutral", "score": 0.0}
    pos = neg = 0
    for i, w in enumerate(words):
        negated = any(prev in config.NEGATIONS for prev in words[max(0, i - 2):i])
        if w in config.POSITIVE_WORDS:
            if negated:
                neg += 1
            else:
                pos += 1
        elif w in config.NEGATIVE_WORDS:
            if negated and w not in {"never"}:
                pos += 0  # "not bad" is only mildly positive; ignore
            else:
                neg += 1
    total = pos + neg
    if total == 0:
        return {"label": "Neutral", "score": 0.0}
    score = round((pos - neg) / total, 2)
    # Require a bit of evidence before calling something strongly one-sided.
    if score <= -0.2:
        label = "Negative"
    elif score >= 0.2:
        label = "Positive"
    else:
        label = "Neutral"
    return {"label": label, "score": score}


def detect_priority(text: str, category: str, sentiment_score: float = 0.0) -> dict:
    low = (text or "").lower()
    high_hits = [t for t in config.HIGH_PRIORITY_TERMS if _contains(low, t)]
    medium_hits = [t for t in config.MEDIUM_PRIORITY_TERMS if _contains(low, t)]

    if high_hits:
        level = "High"
    elif len(medium_hits) >= 2 or (medium_hits and sentiment_score <= -0.2):
        level = "Medium"
    else:
        level = "Low"

    floor = config.CATEGORY_MIN_PRIORITY.get(category)
    if floor and config.PRIORITY_ORDER.index(level) < config.PRIORITY_ORDER.index(floor):
        level = floor
        reasons = [f"'{category}' tickets are at least {floor} priority"]
    else:
        reasons = []

    if high_hits:
        reasons.append("urgency / risk terms: " + ", ".join(high_hits[:4]))
    if medium_hits and level != "High":
        reasons.append("problem terms: " + ", ".join(medium_hits[:4]))
    if not reasons:
        reasons.append("no urgency or problem signals found")

    return {"level": level, "reasons": reasons}
