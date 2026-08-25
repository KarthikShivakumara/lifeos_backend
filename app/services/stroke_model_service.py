from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import HTTPException

from app.schemas.stroke import (
    FeatureContribution,
    StrokeExplanationResponse,
    StrokePredictionRequest,
    StrokePredictionResponse,
)

logger = logging.getLogger("lifeos.stroke_service")

FEATURE_NAME_MAP = {
    "gender": "Biological Sex",
    "age": "Age",
    "hypertension": "Hypertension History",
    "heart_disease": "Heart Disease History",
    "ever_married": "Marital History",
    "work_type": "Employment Classification",
    "Residence_type": "Residence Setting",
    "avg_glucose_level": "Average Blood Glucose",
    "bmi": "Body Mass Index (BMI)",
    "smoking_status": "Smoking History",
}


def classify_risk_level(score: float) -> str:
    if score < 0.30:
        return "low"
    elif score < 0.60:
        return "moderate"
    elif score < 0.80:
        return "high"
    else:
        return "very_high"


class StrokeModelService:
    _instance: StrokeModelService | None = None

    def __init__(self) -> None:
        self.model_loaded = False
        self.artifact: dict[str, Any] = {}
        self.preprocessor = None
        self.model = None
        self.calibrated_model = None
        self.explainer = None
        self.operating_threshold = 0.50
        self._load_artifact()

    @classmethod
    def get_instance(cls) -> StrokeModelService:
        if cls._instance is None:
            cls._instance = StrokeModelService()
        return cls._instance

    def _load_artifact(self) -> None:
        root_dir = Path(__file__).resolve().parents[3]
        model_path = root_dir / "models" / "stroke" / "stroke_final.pkl"

        if not model_path.exists():
            logger.warning(f"Stroke model artifact not found at {model_path}")
            return

        try:
            self.artifact = joblib.load(model_path)
            self.preprocessor = self.artifact.get("preprocessor")
            self.model = self.artifact.get("model")
            self.calibrated_model = self.artifact.get("calibrated_model")
            self.operating_threshold = float(self.artifact.get("operating_threshold", 0.50))

            if self.model is not None:
                self.explainer = shap.TreeExplainer(self.model)
                self.model_loaded = True
                logger.info(f"Stroke model artifact loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load Stroke model artifact: {e}")

    def predict(self, request: StrokePredictionRequest) -> StrokePredictionResponse:
        if not self.model_loaded or self.calibrated_model is None or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="Stroke prediction service is currently unavailable.")

        try:
            input_df = pd.DataFrame([{
                "gender": request.gender,
                "age": request.age,
                "hypertension": request.hypertension,
                "heart_disease": request.heart_disease,
                "ever_married": request.ever_married,
                "work_type": request.work_type,
                "Residence_type": request.Residence_type,
                "avg_glucose_level": request.avg_glucose_level,
                "bmi": request.bmi if request.bmi is not None else np.nan,
                "smoking_status": request.smoking_status,
            }])

            X_trans = self.preprocessor.transform(input_df)
            cal_probs = self.calibrated_model.predict_proba(X_trans)[0]
            prob = float(cal_probs[1])

            risk_level = classify_risk_level(prob)
            prediction = 1 if prob >= self.operating_threshold else 0

            return StrokePredictionResponse(
                disease="stroke",
                risk_score=round(prob, 4),
                risk_level=risk_level,
                threshold=round(self.operating_threshold, 4),
                prediction=prediction,
                model="LightGBM",
                model_version="1.0.0",
            )
        except Exception as e:
            logger.error(f"Error during stroke prediction: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    def explain(self, request: StrokePredictionRequest) -> StrokeExplanationResponse:
        if not self.model_loaded or self.explainer is None or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="Stroke explanation service is currently unavailable.")

        try:
            input_df = pd.DataFrame([{
                "gender": request.gender,
                "age": request.age,
                "hypertension": request.hypertension,
                "heart_disease": request.heart_disease,
                "ever_married": request.ever_married,
                "work_type": request.work_type,
                "Residence_type": request.Residence_type,
                "avg_glucose_level": request.avg_glucose_level,
                "bmi": request.bmi if request.bmi is not None else np.nan,
                "smoking_status": request.smoking_status,
            }])

            X_trans = self.preprocessor.transform(input_df)
            shap_values = self.explainer.shap_values(X_trans)

            if isinstance(shap_values, list):
                sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            elif len(shap_values.shape) == 3:
                sv = shap_values[0, :, 1]
            else:
                sv = shap_values[0]

            bv = float(self.explainer.expected_value[1] if isinstance(self.explainer.expected_value, (list, np.ndarray)) else self.explainer.expected_value)

            raw_feature_names = self.artifact.get("feature_names", list(input_df.columns))
            contributions: list[FeatureContribution] = []

            for idx, feature_name in enumerate(raw_feature_names):
                val = float(sv[idx]) if idx < len(sv) else 0.0
                direction = "increases_risk" if val > 0 else "decreases_risk"
                display_name = FEATURE_NAME_MAP.get(feature_name, feature_name)
                direction_text = "increases estimated model risk" if val > 0 else "decreases estimated model risk"
                hr = f"{display_name} ({feature_name}) {direction_text} (attribution: {val:+.4f})."

                contributions.append(FeatureContribution(
                    feature=feature_name,
                    contribution=round(val, 4),
                    direction=direction,
                    human_readable=hr,
                ))

            contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
            top_3 = [c.human_readable for c in contributions[:3]]
            summary = "Stroke risk attributions driven by: " + "; ".join(top_3) + "."

            return StrokeExplanationResponse(
                disease="stroke",
                base_value=round(bv, 4),
                top_contributions=contributions,
                explanation_summary=summary,
            )
        except Exception as e:
            logger.error(f"Error during stroke explanation: {e}")
            raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")
