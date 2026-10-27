"""
Text preprocessing used by BOTH the ML training pipeline and the live
analysis services, so training and inference always see identical features.

Everything here is pure Python (no NLTK downloads needed) which keeps the
project runnable on a fresh machine with zero extra setup.
"""

import re
import string

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "of", "at", "by",
    "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "will", "would", "should", "could", "can", "i", "me", "my", "you",
    "your", "he", "she", "it", "its", "we", "our", "they", "them", "their",
    "this", "that", "these", "those", "as", "not", "no", "nor", "too", "very",
    "s", "t", "just", "also", "am", "hi", "hello", "dear", "please", "kindly",
    "regards", "thanks", "thank", "team", "support", "sir", "madam", "there",
    "which", "who", "what", "when", "where", "how", "all", "any", "some",
}

# Order matters: longest suffixes first.
_SUFFIXES = ("ingly", "edly", "ing", "ed", "es", "ly", "s")


def clean_text(text: str) -> str:
    """Lowercase, strip URLs / emails / punctuation / digits, collapse spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str):
    return text.split()


def remove_stopwords(tokens):
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def light_stem(token: str) -> str:
    """Very small deterministic suffix stripper (e.g. 'charged' -> 'charg')."""
    if len(token) <= 4:
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            return token[: -len(suf)]
    return token


def stem_tokens(tokens):
    return [light_stem(t) for t in tokens]


def preprocess(text: str) -> str:
    """clean -> tokenize -> remove stopwords -> light stem -> rejoin."""
    tokens = tokenize(clean_text(text))
    tokens = remove_stopwords(tokens)
    tokens = stem_tokens(tokens)
    return " ".join(tokens)
