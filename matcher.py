"""
Ticket <-> Knowledge-Base matching service.

* Builds a TF-IDF index over the help-centre articles ONCE (module level).
* For every ticket, returns the top-K most similar articles using cosine
  similarity, plus issue keywords shared with the best article.
* Finds which details an agent needs but the ticket does not contain
  ("missing information"), and builds recommendations + a draft reply.
"""

import os
import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils import config  # noqa: E402
from backend.services.text_processor import preprocess  # noqa: E402
from backend.services.keyword_extractor import extract_keywords  # noqa: E402


class KnowledgeBase:
    def __init__(self):
        self.articles = []
        self.vectorizer = None
        self.matrix = None
        self.loaded = False
        self.load_error = None
        self._load()

    def _load(self):
        try:
            if not os.path.exists(config.KNOWLEDGE_BASE_PATH):
                raise FileNotFoundError(
                    "knowledge_base.csv not found. Run `python data/make_knowledge_base.py`."
                )
            df = pd.read_csv(config.KNOWLEDGE_BASE_PATH).fillna("")
            self.articles = df.to_dict(orient="records")
            corpus = [preprocess(f"{a['title']} {a['title']} {a['content']}") for a in self.articles]
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            self.matrix = self.vectorizer.fit_transform(corpus)
            self.loaded = True
        except Exception as exc:  # noqa: BLE001
            self.loaded = False
            self.load_error = str(exc)

    def search(self, ticket_text: str, top_k: int = config.TOP_K_ARTICLES, category: str = None):
        """Returns the top_k articles as dicts with a 0-100 relevance score."""
        if not self.loaded:
            return []
        clean = preprocess(ticket_text)
        if not clean.strip():
            return []
        vec = self.vectorizer.transform([clean])
        if vec.nnz == 0:
            return []
        sims = cosine_similarity(vec, self.matrix)[0]
        order = sims.argsort()[::-1][:top_k]
        results = []
        for idx in order:
            a = self.articles[int(idx)]
            results.append({
                "article_id": a["article_id"],
                "title": a["title"],
                "category": a["category"],
                "score": round(float(sims[idx]) * 100, 1),
                "steps": [s.strip() for s in str(a["steps"]).split("|") if s.strip()],
                "same_category": bool(category and a["category"] == category),
            })
        return [r for r in results if r["score"] > 0]


knowledge_base = KnowledgeBase()


# ---------------------------------------------------------------------------
# Missing information
# ---------------------------------------------------------------------------

def find_missing_info(category: str, info: dict, text: str) -> list:
    """Details the agent normally needs for this category but the ticket lacks."""
    required = config.REQUIRED_INFO_BY_CATEGORY.get(category, ["email"])
    missing = []
    for key in required:
        if key == "error_details":
            has = bool(extract_keywords(text) and "Error Message" in extract_keywords(text)) or "error code" in text.lower()
            if not has:
                missing.append(config.INFO_LABELS[key])
        elif key == "device":
            if info.get("device", config.NOT_DETECTED) == config.NOT_DETECTED:
                missing.append(config.INFO_LABELS[key])
        else:
            if info.get(key, config.NOT_DETECTED) == config.NOT_DETECTED:
                missing.append(config.INFO_LABELS[key])
    return missing


# ---------------------------------------------------------------------------
# Recommendations & draft reply
# ---------------------------------------------------------------------------

def generate_recommendations(priority: dict, sentiment: dict, category: str,
                             missing_info: list, top_score: float, articles: list) -> list:
    recs = []
    if priority["level"] == "High":
        recs.append("Escalate: assign to a senior agent and respond within 1 hour.")
    elif priority["level"] == "Medium":
        recs.append("Respond within 8 working hours.")
    else:
        recs.append("Standard queue: respond within 24 hours.")

    if sentiment["label"] == "Negative":
        recs.append("Customer sounds unhappy: open with an apology and acknowledge the inconvenience.")

    for item in missing_info[:4]:
        recs.append(f"Ask the customer for: {item}.")

    if category == "Security & Fraud":
        recs.append("Notify the security team and advise the customer to secure their account.")

    if not articles or top_score < 15:
        recs.append("No strong knowledge-base match: route to a human agent and consider writing a new help article.")
    elif top_score < 35:
        recs.append("Partial knowledge-base match: use the suggested article as a starting point and personalise the reply.")
    else:
        recs.append("Strong knowledge-base match: the suggested article's steps can resolve this ticket.")
    return recs


def build_draft_reply(customer_name: str, category: str, priority: dict,
                      sentiment: dict, articles: list, missing_info: list) -> str:
    name = customer_name if customer_name and customer_name != config.NOT_DETECTED else "there"
    lines = [f"Hi {name},", ""]
    if sentiment["label"] == "Negative":
        lines.append("I'm really sorry for the trouble you've had. I understand how frustrating this must be, and I'll help get it sorted.")
    else:
        lines.append("Thanks for reaching out to us. Here's how we can help.")
    lines.append("")

    if articles:
        best = articles[0]
        lines.append(f"Based on your message, this looks like a '{category}' request. Please try the following ({best['title']}):")
        for i, step in enumerate(best["steps"], 1):
            lines.append(f"  {i}. {step}")
    else:
        lines.append(f"Your request has been logged under '{category}' and our team will review it personally.")

    if missing_info:
        lines += ["", "To help us resolve this faster, could you please share:"]
        lines += [f"  - {m}" for m in missing_info]

    if priority["level"] == "High":
        lines += ["", "We have marked your ticket as high priority and a senior team member will follow up shortly."]
    lines += ["", "Best regards,", "Customer Support Team"]
    return "\n".join(lines)


def full_match(ticket_text: str, category: str, info: dict, priority: dict, sentiment: dict) -> dict:
    """Runs the complete KB-matching pipeline and returns a combined result."""
    articles = knowledge_base.search(ticket_text, category=category)
    top_score = articles[0]["score"] if articles else 0.0

    ticket_keywords = set(extract_keywords(ticket_text))
    matching_keywords = []
    if articles:
        best_text = next(
            (f"{a['title']} {a['content']}" for a in knowledge_base.articles
             if a["article_id"] == articles[0]["article_id"]), "")
        matching_keywords = sorted(ticket_keywords & set(extract_keywords(best_text)))

    missing_info = find_missing_info(category, info, ticket_text)
    recs = generate_recommendations(priority, sentiment, category, missing_info, top_score, articles)
    reply = build_draft_reply(info.get("customer_name"), category, priority, sentiment, articles, missing_info)

    return {
        "match_score": top_score,
        "suggested_articles": articles,
        "matching_keywords": matching_keywords,
        "missing_info": missing_info,
        "recommendations": recs,
        "draft_reply": reply,
    }
