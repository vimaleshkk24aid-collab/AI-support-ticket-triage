"""
FastAPI application entrypoint.

Run with:
    uvicorn backend.main:app --reload

The ML model and the knowledge-base index are loaded once, at import time
(see ml/predict.py and backend/services/matcher.py), never per request.
"""

import logging
import os
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes import analysis, prediction  # noqa: E402
from backend.schemas import HealthResponse  # noqa: E402
from backend.services.matcher import knowledge_base  # noqa: E402
from ml.predict import predictor  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticket-triage-api")

app = FastAPI(
    title="AI Support Ticket Triage & Smart Reply API",
    description="Classifies support tickets, scores priority and sentiment, "
                "finds matching help articles and drafts a reply.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    if predictor.loaded:
        logger.info("Ticket category model loaded successfully.")
    else:
        logger.warning("Category model NOT loaded: %s. Run `python ml/train.py` and restart.", predictor.load_error)
    if knowledge_base.loaded:
        logger.info("Knowledge base loaded: %d articles.", len(knowledge_base.articles))
    else:
        logger.warning("Knowledge base NOT loaded: %s", knowledge_base.load_error)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Safety net: never leak raw stack traces to the client."""
    logger.exception("Unhandled exception while processing %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred while processing your request."})


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        model_loaded=predictor.loaded,
        knowledge_base_loaded=knowledge_base.loaded,
    )


app.include_router(prediction.router, tags=["Prediction"])
app.include_router(analysis.router, tags=["Analysis"])
