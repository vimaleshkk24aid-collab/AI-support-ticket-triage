"""
Shared helpers used by the route modules: upload validation, text
extraction and the single `analyze_text` pipeline so every endpoint
produces consistent results.
"""

import os
import sys
from typing import Optional

from fastapi import HTTPException, UploadFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils import config  # noqa: E402
from backend.services.ticket_parser import (  # noqa: E402
    TicketParsingError, extract_text, extract_ticket_info,
)
from backend.services.keyword_extractor import extract_keywords, keyword_counts  # noqa: E402
from backend.services.analyzer import analyze_sentiment, detect_priority  # noqa: E402
from ml.predict import predictor  # noqa: E402


def validate_upload(filename: str, file_bytes: bytes):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF, DOCX and TXT files are allowed.",
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > config.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {config.MAX_FILE_SIZE_MB} MB.",
        )


async def get_ticket_text(file: Optional[UploadFile], text: Optional[str]) -> str:
    """Ticket text comes from an uploaded file OR a pasted text field."""
    if file is not None and file.filename:
        file_bytes = await file.read()
        validate_upload(file.filename, file_bytes)
        try:
            content = extract_text(file.filename, file_bytes)
        except TicketParsingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    elif text and text.strip():
        content = text
    else:
        raise HTTPException(status_code=400, detail="Provide a ticket file or ticket text.")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Ticket appears to be empty.")
    if len(content) > config.MAX_TEXT_CHARS:
        content = content[: config.MAX_TEXT_CHARS]
    return content


def predict_category(text: str):
    if predictor.loaded:
        try:
            return predictor.predict(text)
        except Exception:  # noqa: BLE001
            pass
    return config.NOT_DETECTED, 0.0, {}


def analyze_text(text: str) -> dict:
    """Runs parsing + ML + rule-based analysis on already-extracted text."""
    info = extract_ticket_info(text)
    category, confidence, probs = predict_category(text)
    sentiment = analyze_sentiment(text)
    priority = detect_priority(text, category, sentiment["score"])
    return {
        "ticket_info": info,
        "category": category,
        "confidence": confidence,
        "category_probabilities": probs,
        "priority": priority,
        "sentiment": sentiment,
        "keywords": extract_keywords(text),
        "keyword_counts": keyword_counts(text),
    }
