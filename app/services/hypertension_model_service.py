from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import shap.explainers._tree as tree_mod
from fastapi import HTTPException

from app.schemas.hypertension import (
    HypertensionExplanationResponse,
    HypertensionFeatureContribution,
    HypertensionHealthCheckResponse,
    HypertensionPredictionRequest,
    HypertensionPredictionResponse,
)


logger = logging.getLogger("lifeos.hypertension_service")

# Apply monkey-patch to SHAP UBJSON decoder for XGBoost 2.x compatibility
_orig_decode_ubjson = tree_mod.decode_ubjson_buffer


def _patched_decode_ubjson(fd: Any) -> Any:
    res = _orig_decode_ubjson(fd)
    if isinstance(res, dict) and "learner" in res:
        lp = res["learner"].get("learner_model_param", {})
        if "base_score" in lp and isinstance(lp["base_score"], str):
            lp["base_score"] = lp["base_score"].strip("[]")
    return res


tree_mod.decode_ubjson_buffer = _patched_decode_ubjson

FEATURE_NAME_MAP = {
    "age_years": "Age",
    "sex": "Biological Sex",
    "bmi": "Body Mass Index (BMI)",
    "systolic_bp_mmHg": "Systolic Blood Pressure",
    "diastolic_bp_mmHg": "Diastolic Blood Pressure",
    "heart_rate": "Heart Rate",
    "cholesterol": "Total Cholesterol",
    "glucose": "Blood Glucose",
    "smoking_status": "Smoking Status",
    "physical_activity": "Physical Activity Level",
    "stress_level": "Stress Level",
}


class HypertensionModelService:
    _instance: HypertensionModelService | None = None

    def __init__(self) -> None:
        self.artifact: dict[str, Any] | None = None
        self.imputer: Any = None
        self.uncalibrated_model: Any = None
        self.calibrated_model: Any = None
        self.explainer: Any = None
        self.threshold: float = 0.60
        self.feature_cols: list[str] = [
            "age_years",
            "sex",
            "bmi",
            "systolic_bp_mmHg",
            "diastolic_bp_mmHg",
            "heart_rate",
            "cholesterol",
            "glucose",
            "smoking_status",
            "physical_activity",
            "stress_level",
        ]
        self.model_name: str = "XGBoost"
        self.model_version: str = "1.0.0"
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> HypertensionModelService:
        if cls._instance is None:
            cls._instance = HypertensionModelService()
        return cls._instance

    def load_model(self) -> None:
        if self.is_loaded:
            return

        candidate_paths = [
            Path(__file__).resolve().parents[3] / "models" / "hypertension" / "hypertension_final.pkl",
            Path(__file__).resolve().parents[2] / "models" / "hypertension" / "hypertension_final.pkl",
            Path("models/hypertension/hypertension_final.pkl"),
            Path("../models/hypertension/hypertension_final.pkl"),
        ]

        model_path: Path | None = None
        for p in candidate_paths:
            if p.exists():
                model_path = p
                break

        if model_path is None:
            logger.error("Failed to locate models/hypertension/hypertension_final.pkl")
            raise FileNotFoundError("models/hypertension/hypertension_final.pkl artifact not found.")

        logger.info("Loading Hypertension final model from: %s", model_path)
        self.artifact = joblib.load(model_path)
        self.imputer = self.artifact["imputer"]
        self.uncalibrated_model = self.artifact["uncalibrated_model"]
        self.calibrated_model = self.artifact["calibrated_model"]
        self.threshold = float(self.artifact.get("operating_threshold", 0.60))
        self.feature_cols = self.artifact.get("features", self.feature_cols)
        self.model_name = self.artifact.get("model_type", "XGBoost")
        self.model_version = self.artifact.get("model_version", "1.0.0")

        # Initialize SHAP TreeExplainer from base XGBoost model
        if self.uncalibrated_model is not None:
            try:
                booster = self.uncalibrated_model.get_booster()
                self.explainer = shap.TreeExplainer(booster)
                logger.info("Hypertension SHAP TreeExplainer initialized successfully.")
            except Exception as err:
                logger.warning("Failed to initialize Hypertension SHAP TreeExplainer: %s", err)

        self.is_loaded = True
        logger.info("Hypertension model loaded successfully.")

    def get_health_status(self) -> HypertensionHealthCheckResponse:
        if not self.is_loaded:
            try:
                self.load_model()
            except Exception:
                return HypertensionHealthCheckResponse(
                    status="error",
                    hypertension_model="not_loaded",
                    model="XGBoost",
                    version="1.0.0",
                )
        return HypertensionHealthCheckResponse(
            status="ok",
            hypertension_model="loaded",
            model=self.model_name,
            version=self.model_version,
        )

    def prepare_input_dataframe(self, req: HypertensionPredictionRequest) -> pd.DataFrame:
        data_dict = req.model_dump()
        df = pd.DataFrame([data_dict])
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        return df[self.feature_cols]

    def predict(self, req: HypertensionPredictionRequest) -> HypertensionPredictionResponse:
        if not self.is_loaded:
            self.load_model()

        try:
            df = self.prepare_input_dataframe(req)
            X_trans = self.imputer.transform(df)
            probs = self.calibrated_model.predict_proba(X_trans)[:, 1]
            risk_score = round(float(probs[0]), 4)
            prediction = int(risk_score >= self.threshold)

            # Prototype risk bands
            if risk_score < 0.30:
                risk_level = "low"
            elif risk_score < self.threshold:
                risk_level = "moderate"
            else:
                risk_level = "high"

            return HypertensionPredictionResponse(
                disease="hypertension",
                risk_score=risk_score,
                risk_level=risk_level,
                threshold=self.threshold,
                prediction=prediction,
                model=self.model_name,
                model_version=self.model_version,
            )
        except Exception as err:
            logger.error("Prediction failed: %s", err, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Hypertension prediction execution failed: {str(err)}")

    def explain(self, req: HypertensionPredictionRequest) -> HypertensionExplanationResponse:
        if not self.is_loaded:
            self.load_model()

        pred_resp = self.predict(req)
        df = self.prepare_input_dataframe(req)

        top_contributors: list[HypertensionFeatureContribution] = []

        if self.imputer is not None and self.explainer is not None:
            try:
                X_trans = self.imputer.transform(df)
                shap_vals = self.explainer.shap_values(X_trans)[0]

                # Pair feature names with SHAP values
                pairs = sorted(zip(self.feature_cols, shap_vals), key=lambda x: abs(x[1]), reverse=True)

                for feat_name, val in pairs[:5]:
                    contrib_val = round(float(val), 4)
                    direction = "increases_risk" if contrib_val > 0 else "decreases_risk"
                    display_name = FEATURE_NAME_MAP.get(feat_name, feat_name)

                    if direction == "increases_risk":
                        human_msg = f"{display_name} contributed significantly to increasing the model's estimated risk score."
                    else:
                        human_msg = f"{display_name} contributed to lowering the model's estimated risk score."

                    top_contributors.append(
                        HypertensionFeatureContribution(
                            feature=feat_name,
                            contribution=contrib_val,
                            direction=direction,
                            human_readable=human_msg,
                        )
                    )
            except Exception as err:
                logger.warning("Hypertension SHAP attribution failed: %s", err)

        return HypertensionExplanationResponse(
            disease="hypertension",
            risk_score=pred_resp.risk_score,
            risk_level=pred_resp.risk_level,
            threshold=pred_resp.threshold,
            prediction=pred_resp.prediction,
            model=pred_resp.model,
            model_version=pred_resp.model_version,
            top_contributors=top_contributors,
        )


hypertension_service = HypertensionModelService.get_instance()
