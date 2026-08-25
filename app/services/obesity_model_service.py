from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import HTTPException

from app.schemas.obesity import (
    ObesityExplanationResponse,
    ObesityFeatureContribution,
    ObesityHealthCheckResponse,
    ObesityPredictionRequest,
    ObesityPredictionResponse,
)


logger = logging.getLogger("lifeos.obesity_service")

FEATURE_NAME_MAP = {
    "age_years": "Age",
    "sex": "Biological Sex",
    "family_history_obesity": "Family History of Obesity",
    "frequent_high_calorie_food": "High Calorie Food Consumption",
    "vegetable_consumption": "Vegetable Consumption Frequency",
    "meals_per_day": "Main Meals Per Day",
    "between_meal_eating": "Food Between Meals Frequency",
    "smoking_status": "Smoking Status",
    "water_intake_l": "Daily Water Intake (Liters)",
    "calorie_monitoring": "Calorie Consumption Monitoring",
    "physical_activity_frequency": "Physical Activity Frequency",
    "technology_usage_hours": "Screen / Technology Device Hours",
    "alcohol_use": "Alcohol Consumption",
    "transportation_mode": "Sedentary Transportation Mode",
}


class ObesityModelService:
    _instance: ObesityModelService | None = None

    def __init__(self) -> None:
        self.artifact: dict[str, Any] | None = None
        self.imputer: Any = None
        self.uncalibrated_model: Any = None
        self.calibrated_model: Any = None
        self.explainer: Any = None
        self.threshold: float = 0.50
        self.feature_cols: list[str] = [
            "age_years",
            "sex",
            "family_history_obesity",
            "frequent_high_calorie_food",
            "vegetable_consumption",
            "meals_per_day",
            "between_meal_eating",
            "smoking_status",
            "water_intake_l",
            "calorie_monitoring",
            "physical_activity_frequency",
            "technology_usage_hours",
            "alcohol_use",
            "transportation_mode",
        ]
        self.model_name: str = "LightGBM"
        self.model_version: str = "1.0.0"
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> ObesityModelService:
        if cls._instance is None:
            cls._instance = ObesityModelService()
        return cls._instance

    def load_model(self) -> None:
        if self.is_loaded:
            return

        candidate_paths = [
            Path(__file__).resolve().parents[3] / "models" / "obesity" / "obesity_final.pkl",
            Path(__file__).resolve().parents[2] / "models" / "obesity" / "obesity_final.pkl",
            Path("models/obesity/obesity_final.pkl"),
            Path("../models/obesity/obesity_final.pkl"),
        ]

        model_path: Path | None = None
        for p in candidate_paths:
            if p.exists():
                model_path = p
                break

        if model_path is None:
            logger.error("Failed to locate models/obesity/obesity_final.pkl")
            raise FileNotFoundError("models/obesity/obesity_final.pkl artifact not found.")

        logger.info("Loading Obesity final model from: %s", model_path)
        self.artifact = joblib.load(model_path)
        self.imputer = self.artifact["imputer"]
        self.uncalibrated_model = self.artifact["uncalibrated_model"]
        self.calibrated_model = self.artifact["calibrated_model"]
        self.threshold = float(self.artifact.get("operating_threshold", 0.50))
        self.feature_cols = self.artifact.get("features", self.feature_cols)
        self.model_name = self.artifact.get("model_type", "LightGBM")
        self.model_version = self.artifact.get("model_version", "1.0.0")

        # Initialize SHAP TreeExplainer from base LightGBM model
        if self.uncalibrated_model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.uncalibrated_model)
                logger.info("Obesity SHAP TreeExplainer initialized successfully.")
            except Exception as err:
                logger.warning("Failed to initialize Obesity SHAP TreeExplainer: %s", err)

        self.is_loaded = True
        logger.info("Obesity model loaded successfully.")

    def get_health_status(self) -> ObesityHealthCheckResponse:
        if not self.is_loaded:
            try:
                self.load_model()
            except Exception:
                return ObesityHealthCheckResponse(
                    status="error",
                    obesity_model="not_loaded",
                    model="LightGBM",
                    version="1.0.0",
                )
        return ObesityHealthCheckResponse(
            status="ok",
            obesity_model="loaded",
            model=self.model_name,
            version=self.model_version,
        )

    def prepare_input_dataframe(self, req: ObesityPredictionRequest) -> pd.DataFrame:
        data_dict = req.model_dump()
        df = pd.DataFrame([data_dict])
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        return df[self.feature_cols]

    def predict(self, req: ObesityPredictionRequest) -> ObesityPredictionResponse:
        if not self.is_loaded:
            self.load_model()

        try:
            df = self.prepare_input_dataframe(req)
            X_trans = self.imputer.transform(df)
            probs = self.calibrated_model.predict_proba(X_trans)[:, 1]
            risk_score = round(float(probs[0]), 4)
            prediction = int(risk_score >= self.threshold)

            # Prototype risk bands
            if risk_score < 0.25:
                risk_level = "low"
            elif risk_score < self.threshold:
                risk_level = "moderate"
            else:
                risk_level = "high"

            return ObesityPredictionResponse(
                disease="obesity",
                risk_score=risk_score,
                risk_level=risk_level,
                threshold=self.threshold,
                prediction=prediction,
                model=self.model_name,
                model_version=self.model_version,
            )
        except Exception as err:
            logger.error("Prediction failed: %s", err, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Obesity prediction execution failed: {str(err)}")

    def explain(self, req: ObesityPredictionRequest) -> ObesityExplanationResponse:
        if not self.is_loaded:
            self.load_model()

        pred_resp = self.predict(req)
        df = self.prepare_input_dataframe(req)

        top_contributors: list[ObesityFeatureContribution] = []

        if self.imputer is not None and self.explainer is not None:
            try:
                X_trans = self.imputer.transform(df)
                shap_vals = self.explainer.shap_values(X_trans)

                # Handle LightGBM binary output format in SHAP
                if isinstance(shap_vals, list):
                    vals = shap_vals[1][0]
                elif len(shap_vals.shape) == 3:
                    vals = shap_vals[0, :, 1]
                else:
                    vals = shap_vals[0]

                pairs = sorted(zip(self.feature_cols, vals), key=lambda x: abs(x[1]), reverse=True)

                for feat_name, val in pairs[:5]:
                    contrib_val = round(float(val), 4)
                    direction = "increases_risk" if contrib_val > 0 else "decreases_risk"
                    display_name = FEATURE_NAME_MAP.get(feat_name, feat_name)

                    if direction == "increases_risk":
                        human_msg = f"{display_name} contributed to increasing the model's estimated obesity risk score."
                    else:
                        human_msg = f"{display_name} contributed to lowering the model's estimated obesity risk score."

                    top_contributors.append(
                        ObesityFeatureContribution(
                            feature=feat_name,
                            contribution=contrib_val,
                            direction=direction,
                            human_readable=human_msg,
                        )
                    )
            except Exception as err:
                logger.warning("Obesity SHAP attribution failed: %s", err)

        return ObesityExplanationResponse(
            disease="obesity",
            risk_score=pred_resp.risk_score,
            risk_level=pred_resp.risk_level,
            threshold=pred_resp.threshold,
            prediction=pred_resp.prediction,
            model=pred_resp.model,
            model_version=pred_resp.model_version,
            top_contributors=top_contributors,
        )


obesity_service = ObesityModelService.get_instance()
