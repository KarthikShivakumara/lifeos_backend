from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import HTTPException

from app.schemas.sleep import (
    FeatureContribution,
    SleepExplanationResponse,
    SleepPredictionRequest,
    SleepPredictionResponse,
)

logger = logging.getLogger("lifeos.sleep_service")

FEATURE_NAME_MAP = {
    "Gender": "Biological Sex",
    "Age": "Age",
    "Occupation": "Occupation",
    "Sleep Duration": "Sleep Duration",
    "Quality of Sleep": "Quality of Sleep",
    "Physical Activity Level": "Physical Activity Level",
    "Stress Level": "Stress Level",
    "BMI Category": "BMI Category",
    "systolic_bp": "Systolic Blood Pressure",
    "diastolic_bp": "Diastolic Blood Pressure",
    "Heart Rate": "Resting Heart Rate",
    "Daily Steps": "Daily Step Count",
}


def classify_sleep_risk_level(score: float) -> str:
    if score < 0.40:
        return "low"
    elif score < 0.65:
        return "moderate"
    else:
        return "elevated"


class SleepModelService:
    _instance: SleepModelService | None = None

    def __init__(self) -> None:
        self.model_loaded = False
        self.artifact: dict[str, Any] = {}
        self.preprocessor = None
        self.model = None
        self.calibrated_model = None
        self.explainer = None
        self.operating_threshold = 0.65
        self._load_artifact()

    @classmethod
    def get_instance(cls) -> SleepModelService:
        if cls._instance is None:
            cls._instance = SleepModelService()
        return cls._instance

    def _load_artifact(self) -> None:
        possible_paths = [
            Path(__file__).resolve().parents[2] / "models" / "sleep" / "sleep_final.pkl",
            Path(__file__).resolve().parents[3] / "models" / "sleep" / "sleep_final.pkl",
        ]
        model_path = next((p for p in possible_paths if p.exists()), possible_paths[0])

        if not model_path.exists():
            logger.warning(f"Sleep model artifact not found at {model_path}")
            return

        try:
            self.artifact = joblib.load(model_path)
            self.preprocessor = self.artifact.get("preprocessor")
            self.model = self.artifact.get("model")
            self.calibrated_model = self.artifact.get("calibrated_model")
            self.operating_threshold = float(self.artifact.get("operating_threshold", 0.65))

            if self.model is not None:
                self.model_loaded = True
                logger.info(f"Sleep model artifact loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load Sleep model artifact: {e}")

    def predict(self, request: SleepPredictionRequest) -> SleepPredictionResponse:
        if not self.model_loaded or self.calibrated_model is None or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="Sleep prediction service is currently unavailable.")

        try:
            bmi_cat = "Normal" if request.bmi_category.strip() == "Normal Weight" else request.bmi_category.strip()

            input_df = pd.DataFrame([{
                "Gender": request.gender,
                "Age": request.age,
                "Occupation": request.occupation,
                "Sleep Duration": request.sleep_duration,
                "Quality of Sleep": request.quality_of_sleep,
                "Physical Activity Level": request.physical_activity_level,
                "Stress Level": request.stress_level,
                "BMI Category": bmi_cat,
                "systolic_bp": request.systolic_bp,
                "diastolic_bp": request.diastolic_bp,
                "Heart Rate": request.heart_rate,
                "Daily Steps": request.daily_steps,
            }])

            X_trans = self.preprocessor.transform(input_df)
            cal_probs = self.calibrated_model.predict_proba(X_trans)[0]
            prob = float(cal_probs[1])

            risk_level = classify_sleep_risk_level(prob)
            prediction = 1 if prob >= self.operating_threshold else 0

            return SleepPredictionResponse(
                subsystem="sleep_wellness",
                risk_score=round(prob, 4),
                risk_level=risk_level,
                threshold=round(self.operating_threshold, 4),
                prediction=prediction,
                model="Logistic Regression",
                model_version="1.0.0",
            )
        except Exception as e:
            logger.error(f"Error during Sleep prediction: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    def explain(self, request: SleepPredictionRequest) -> SleepExplanationResponse:
        if not self.model_loaded or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="Sleep explanation service is currently unavailable.")

        try:
            bmi_cat = "Normal" if request.bmi_category.strip() == "Normal Weight" else request.bmi_category.strip()

            input_df = pd.DataFrame([{
                "Gender": request.gender,
                "Age": request.age,
                "Occupation": request.occupation,
                "Sleep Duration": request.sleep_duration,
                "Quality of Sleep": request.quality_of_sleep,
                "Physical Activity Level": request.physical_activity_level,
                "Stress Level": request.stress_level,
                "BMI Category": bmi_cat,
                "systolic_bp": request.systolic_bp,
                "diastolic_bp": request.diastolic_bp,
                "Heart Rate": request.heart_rate,
                "Daily Steps": request.daily_steps,
            }])

            X_trans = self.preprocessor.transform(input_df)
            feature_names = self.artifact.get("feature_names", list(input_df.columns))

            if self.model is not None and hasattr(self.model, "coef_"):
                coefs = self.model.coef_[0]
                intercept = float(self.model.intercept_[0]) if hasattr(self.model, "intercept_") else 0.0
                sv = coefs[:len(feature_names)] * X_trans[0][:len(feature_names)]
                bv = intercept
            else:
                sv = np.zeros(len(feature_names))
                bv = 0.0

            contributions: list[FeatureContribution] = []

            for idx, feature_name in enumerate(feature_names):
                val = float(sv[idx]) if idx < len(sv) else 0.0
                direction = "increases_risk" if val > 0 else "decreases_risk"
                display_name = FEATURE_NAME_MAP.get(feature_name, feature_name)
                direction_text = "increases estimated sleep risk" if val > 0 else "decreases estimated sleep risk"
                hr = f"{display_name} ({feature_name}) {direction_text} (attribution: {val:+.4f})."

                contributions.append(FeatureContribution(
                    feature=feature_name,
                    contribution=round(val, 4),
                    direction=direction,
                    human_readable=hr,
                ))

            contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
            top_3 = [c.human_readable for c in contributions[:3]]
            summary = "Sleep wellness risk attributions driven by: " + "; ".join(top_3) + "."

            return SleepExplanationResponse(
                subsystem="sleep_wellness",
                base_value=round(bv, 4),
                top_contributions=contributions,
                explanation_summary=summary,
            )
        except Exception as e:
            logger.error(f"Error during Sleep explanation: {e}")
            raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

    def to_wellness_signal(self, request: SleepPredictionRequest) -> Any:
        from app.schemas.wellness import WellnessFactor, WellnessSignal

        pred = self.predict(request)
        exp = self.explain(request)

        factors = [
            WellnessFactor(
                feature=c.feature,
                contribution=c.contribution,
                direction=c.direction,
                human_readable=c.human_readable,
            )
            for c in exp.top_contributions[:3]
        ]

        return WellnessSignal(
            domain="sleep",
            score=pred.risk_score,
            level=pred.risk_level,
            status=f"sleep_wellness_{pred.risk_level}",
            top_factors=factors,
            source="calibrated_logistic_regression",
            metadata={
                "operating_threshold": pred.threshold,
                "prediction": pred.prediction,
                "model_version": pred.model_version,
            },
        )
