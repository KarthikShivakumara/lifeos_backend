from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import HTTPException

from app.schemas.diabetes import (
    DiabetesExplanationResponse,
    DiabetesFeatureContribution,
    DiabetesHealthCheckResponse,
    DiabetesPredictionRequest,
    DiabetesPredictionResponse,
)


logger = logging.getLogger("lifeos.diabetes_service")

FEATURE_NAME_MAP = {
    "age_years": "Age",
    "sex": "Biological Sex",
    "bmi": "Body Mass Index (BMI)",
    "blood_glucose_level": "Blood Glucose Level",
    "hba1c_level": "HbA1c Level",
    "hypertension": "Hypertension",
    "heart_disease": "Heart Disease History",
    "smoking_status": "Smoking Status",
}


class DiabetesModelService:
    _instance: DiabetesModelService | None = None

    def __init__(self) -> None:
        self.artifact: dict[str, Any] | None = None
        self.imputer: Any = None
        self.uncalibrated_model: Any = None
        self.calibrated_model: Any = None
        self.explainer: Any = None
        self.threshold: float = 0.70
        self.feature_cols: list[str] = [
            "age_years",
            "sex",
            "bmi",
            "blood_glucose_level",
            "hba1c_level",
            "hypertension",
            "heart_disease",
            "smoking_status",
        ]
        self.model_name: str = "LightGBM"
        self.model_version: str = "1.0.0"
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> DiabetesModelService:
        if cls._instance is None:
            cls._instance = DiabetesModelService()
        return cls._instance

    def load_model(self) -> None:
        if self.is_loaded:
            return

        candidate_paths = [
            Path(__file__).resolve().parents[3] / "models" / "diabetes" / "diabetes_final.pkl",
            Path(__file__).resolve().parents[2] / "models" / "diabetes" / "diabetes_final.pkl",
            Path("models/diabetes/diabetes_final.pkl"),
            Path("../models/diabetes/diabetes_final.pkl"),
        ]

        model_path: Path | None = None
        for p in candidate_paths:
            if p.exists():
                model_path = p
                break

        if model_path is None:
            logger.error("Failed to locate models/diabetes/diabetes_final.pkl")
            raise FileNotFoundError("models/diabetes/diabetes_final.pkl artifact not found.")

        logger.info("Loading Diabetes final model from: %s", model_path)
        self.artifact = joblib.load(model_path)
        self.imputer = self.artifact["imputer"]
        self.uncalibrated_model = self.artifact["uncalibrated_model"]
        self.calibrated_model = self.artifact["calibrated_model"]
        self.threshold = float(self.artifact.get("operating_threshold", 0.70))
        self.feature_cols = self.artifact.get("features", self.feature_cols)
        self.model_name = self.artifact.get("model_type", "LightGBM")
        self.model_version = self.artifact.get("model_version", "1.0.0")

        # Initialize SHAP TreeExplainer from uncalibrated LightGBM model
        if self.uncalibrated_model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.uncalibrated_model)
                logger.info("Diabetes SHAP TreeExplainer initialized successfully.")
            except Exception as err:
                logger.warning("Failed to initialize Diabetes SHAP TreeExplainer: %s", err)

        self.is_loaded = True
        logger.info("Diabetes model loaded successfully.")

    def get_health_status(self) -> DiabetesHealthCheckResponse:
        if not self.is_loaded:
            try:
                self.load_model()
            except Exception:
                return DiabetesHealthCheckResponse(
                    status="error",
                    diabetes_model="not_loaded",
                    model="LightGBM",
                    version="1.0.0",
                )
        return DiabetesHealthCheckResponse(
            status="ok",
            diabetes_model="loaded",
            model=self.model_name,
            version=self.model_version,
        )

    def prepare_input_dataframe(self, req: DiabetesPredictionRequest) -> pd.DataFrame:
        data_dict = req.model_dump()
        df = pd.DataFrame([data_dict])
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        return df[self.feature_cols]

    def predict(self, req: DiabetesPredictionRequest) -> DiabetesPredictionResponse:
        if not self.is_loaded:
            self.load_model()

        try:
            df = self.prepare_input_dataframe(req)
            X_trans = self.imputer.transform(df)
            probs = self.calibrated_model.predict_proba(X_trans)[:, 1]
            risk_score = round(float(probs[0]), 4)
            prediction = int(risk_score >= self.threshold)

            # Prototype risk bands
            if risk_score < (self.threshold / 2):  # < 0.35
                risk_level = "low"
            elif risk_score < self.threshold:  # 0.35 - 0.69
                risk_level = "moderate"
            else:  # >= 0.70
                risk_level = "high"

            return DiabetesPredictionResponse(
                disease="diabetes",
                risk_score=risk_score,
                risk_level=risk_level,
                threshold=self.threshold,
                prediction=prediction,
                model=self.model_name,
                model_version=self.model_version,
            )
        except Exception as err:
            logger.error("Prediction failed: %s", err, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Diabetes prediction execution failed: {str(err)}")

    def explain(self, req: DiabetesPredictionRequest) -> DiabetesExplanationResponse:
        if not self.is_loaded:
            self.load_model()

        pred_resp = self.predict(req)
        df = self.prepare_input_dataframe(req)

        top_contributors: list[DiabetesFeatureContribution] = []

        if self.imputer is not None and self.explainer is not None:
            try:
                X_trans = self.imputer.transform(df)
                shap_vals = self.explainer.shap_values(X_trans)

                if isinstance(shap_vals, list):
                    vals = shap_vals[1][0]
                else:
                    vals = shap_vals[0]

                # Pair feature names with SHAP values
                pairs = sorted(zip(self.feature_cols, vals), key=lambda x: abs(x[1]), reverse=True)

                for feat_name, val in pairs[:5]:
                    contrib_val = round(float(val), 4)
                    direction = "increases_risk" if contrib_val > 0 else "decreases_risk"
                    display_name = FEATURE_NAME_MAP.get(feat_name, feat_name)

                    if direction == "increases_risk":
                        human_msg = f"{display_name} contributed significantly to increasing the model's estimated risk score."
                    else:
                        human_msg = f"{display_name} contributed to lowering the model's estimated risk score."

                    top_contributors.append(
                        DiabetesFeatureContribution(
                            feature=feat_name,
                            contribution=contrib_val,
                            direction=direction,
                            human_readable=human_msg,
                        )
                    )
            except Exception as err:
                logger.warning("Diabetes SHAP attribution failed: %s", err)

        return DiabetesExplanationResponse(
            disease="diabetes",
            risk_score=pred_resp.risk_score,
            risk_level=pred_resp.risk_level,
            threshold=pred_resp.threshold,
            prediction=pred_resp.prediction,
            model=pred_resp.model,
            model_version=pred_resp.model_version,
            top_contributors=top_contributors,
        )


diabetes_service = DiabetesModelService.get_instance()
