"""
Pydantic models used to validate FastAPI requests and responses.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool = False
    knowledge_base_loaded: bool = False


class ErrorResponse(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    category: str
    confidence: float = Field(..., ge=0, le=1)
    category_probabilities: Dict[str, float]


# ---------------------------------------------------------------------------
# /analyze-ticket
# ---------------------------------------------------------------------------

class TicketInfo(BaseModel):
    customer_name: str
    email: str
    phone: str
    order_id: str
    amount: str
    subject: str
    device: str


class Priority(BaseModel):
    level: str
    reasons: List[str]


class Sentiment(BaseModel):
    label: str
    score: float


class AnalyzeTicketResponse(BaseModel):
    ticket_info: TicketInfo
    category: str
    confidence: float
    category_probabilities: Dict[str, float]
    priority: Priority
    sentiment: Sentiment
    keywords: List[str]
    keyword_counts: Dict[str, int]


# ---------------------------------------------------------------------------
# /match-kb
# ---------------------------------------------------------------------------

class MatchKBRequest(BaseModel):
    ticket_text: str


class SuggestedArticle(BaseModel):
    article_id: str
    title: str
    category: str
    score: float
    steps: List[str]
    same_category: bool = False


class MatchKBResponse(BaseModel):
    match_score: float = Field(..., ge=0, le=100)
    suggested_articles: List[SuggestedArticle]


# ---------------------------------------------------------------------------
# /full-analysis
# ---------------------------------------------------------------------------

class FullAnalysisResponse(BaseModel):
    ticket_info: TicketInfo
    category: str
    confidence: float
    category_probabilities: Dict[str, float]
    priority: Priority
    sentiment: Sentiment
    keywords: List[str]
    keyword_counts: Dict[str, int]
    match_score: float
    suggested_articles: List[SuggestedArticle]
    matching_keywords: List[str]
    missing_info: List[str]
    recommendations: List[str]
    draft_reply: str
    ticket_text: str
