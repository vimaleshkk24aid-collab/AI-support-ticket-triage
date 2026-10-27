"""
Routes:
    POST /analyze-ticket -- file or text -> info, category, priority, sentiment, keywords
    POST /match-kb       -- ticket text (JSON) -> best knowledge-base articles
    POST /full-analysis  -- file or text -> complete triage report + draft reply
"""

import os
import sys
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.schemas import (  # noqa: E402
    AnalyzeTicketResponse, FullAnalysisResponse, MatchKBRequest, MatchKBResponse,
)
from backend.routes.pipeline import analyze_text, get_ticket_text  # noqa: E402
from backend.services.matcher import full_match, knowledge_base  # noqa: E402

router = APIRouter()


@router.post("/analyze-ticket", response_model=AnalyzeTicketResponse)
async def analyze_ticket(
    file: Optional[UploadFile] = File(None),
    ticket_text: Optional[str] = Form(None),
):
    text = await get_ticket_text(file, ticket_text)
    return AnalyzeTicketResponse(**analyze_text(text))


@router.post("/match-kb", response_model=MatchKBResponse)
async def match_kb(payload: MatchKBRequest):
    if not payload.ticket_text or not payload.ticket_text.strip():
        raise HTTPException(status_code=400, detail="Ticket text must not be empty.")
    if not knowledge_base.loaded:
        raise HTTPException(status_code=503, detail=f"Knowledge base unavailable: {knowledge_base.load_error}")
    articles = knowledge_base.search(payload.ticket_text)
    return MatchKBResponse(
        match_score=articles[0]["score"] if articles else 0.0,
        suggested_articles=articles,
    )


@router.post("/full-analysis", response_model=FullAnalysisResponse)
async def full_analysis(
    file: Optional[UploadFile] = File(None),
    ticket_text: Optional[str] = Form(None),
):
    text = await get_ticket_text(file, ticket_text)
    analysis = analyze_text(text)
    match = full_match(
        text,
        analysis["category"],
        analysis["ticket_info"],
        analysis["priority"],
        analysis["sentiment"],
    )
    return FullAnalysisResponse(**analysis, **match, ticket_text=text)
