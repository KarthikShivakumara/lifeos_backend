from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.schemas.activity import (
    ActivityCaloriePredictionResponse,
    ActivityEngineInput,
    ActivityPredictionRequest,
    ActivitySignal,
)
from app.services.activity import activity_engine

logger = logging.getLogger("lifeos.activity_api")
router = APIRouter(prefix="/activity", tags=["Physical Activity Intelligence"])

ARTIFACT_PATH = Path(__file__).resolve().parents[4] / "models" / "activity" / "activity_calorie_final.pkl"
_activity_artifact = None


def get_activity_model():
    global _activity_artifact
    if _activity_artifact is None:
        if not ARTIFACT_PATH.exists():
            alt_path = Path("models/activity/activity_calorie_final.pkl")
            if alt_path.exists():
                with open(alt_path, "rb") as f:
                    _activity_artifact = pickle.load(f)
            else:
                logger.error(f"Activity calorie artifact not found at {ARTIFACT_PATH}")
                raise HTTPException(status_code=503, detail="Activity calorie model artifact unavailable")
        else:
            with open(ARTIFACT_PATH, "rb") as f:
                _activity_artifact = pickle.load(f)
    return _activity_artifact


@router.post("/estimate-calories", response_model=ActivityCaloriePredictionResponse, summary="Estimate Workout Energy Expenditure")
def estimate_calories(req: ActivityPredictionRequest) -> ActivityCaloriePredictionResponse:
    """Estimates workout calories burned using the validated LightGBM regression model (R² = 0.9963)."""
    artifact = get_activity_model()
    preprocessor = artifact["preprocessor"]
    model = artifact["model"]

    sample_df = pd.DataFrame([{
        "Gender": req.gender.lower(),
        "Age": req.age,
        "Height": req.height,
        "Weight": req.weight,
        "Duration": req.duration,
        "Heart_Rate": req.heart_rate,
        "Body_Temp": req.body_temp,
    }])

    try:
        trans = preprocessor.transform(sample_df)
        pred_cal = float(model.predict(trans)[0])
        pred_cal = round(max(5.0, pred_cal), 1)
        return ActivityCaloriePredictionResponse(
            subsystem="activity_wellness",
            estimated_calories=pred_cal,
            duration_minutes=req.duration,
            model="LightGBM Regressor",
            model_version="1.0.0",
        )
    except Exception as err:
        logger.error(f"Calorie prediction error: {err}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(err)}")


@router.post("/evaluate", response_model=ActivitySignal, summary="Evaluate Daily Physical Activity Signal")
def evaluate_activity(req: ActivityEngineInput) -> ActivitySignal:
    """Evaluates daily steps, active minutes, and sedentary risk against WHO/CDC physical activity guidelines."""
    return activity_engine.evaluate_activity(req)
