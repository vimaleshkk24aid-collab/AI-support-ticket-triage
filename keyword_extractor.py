"""
Issue-keyword extraction (rule-based).

Looks for known issue terms from utils.config.ISSUE_KEYWORDS using
word-boundary regexes so e.g. "bill" doesn't match inside "billion".
"""

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.config import ISSUE_KEYWORDS  # noqa: E402


def _compile_patterns():
    patterns = {}
    for canonical, variants in ISSUE_KEYWORDS.items():
        escaped = [re.escape(v.strip()) for v in sorted(variants, key=len, reverse=True)]
        pattern = r"(?<![a-zA-Z0-9])(" + "|".join(escaped) + r")(?![a-zA-Z0-9])"
        patterns[canonical] = re.compile(pattern, flags=re.IGNORECASE)
    return patterns


_PATTERNS = _compile_patterns()


def extract_keywords(text: str) -> list:
    """Sorted list of canonical issue keywords found in the text."""
    if not text:
        return []
    return sorted(k for k, p in _PATTERNS.items() if p.search(text))


def keyword_counts(text: str) -> dict:
    """{canonical keyword: number of mentions}."""
    if not text:
        return {}
    counts = {}
    for k, p in _PATTERNS.items():
        n = len(p.findall(text))
        if n:
            counts[k] = n
    return counts
