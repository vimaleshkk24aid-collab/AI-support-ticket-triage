"""
POST /predict -- predicts the ticket category from a file OR pasted text.
"""

import os
import sys
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.schemas import PredictionResponse  # noqa: E402
from backend.routes.pipeline import get_ticket_text  # noqa: E402
from ml.predict import predictor  # noqa: E402

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_ticket_category(
    file: Optional[UploadFile] = File(None),
    ticket_text: Optional[str] = Form(None),
):
    if not predictor.loaded:
        raise HTTPException(
            status_code=503,
            detail="The prediction model is not available. Run `python ml/train.py` "
                   "on the server and restart the backend.",
        )
    text = await get_ticket_text(file, ticket_text)
    try:
        category, confidence, probs = predictor.predict(text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Prediction failed unexpectedly.") from exc
    return PredictionResponse(category=category, confidence=confidence, category_probabilities=probs)
