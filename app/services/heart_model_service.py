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

from app.schemas.heart import (
    FeatureContribution,
    HealthCheckResponse,
    HeartExplanationResponse,
    HeartPredictionRequest,
    HeartPredictionResponse,
)


logger = logging.getLogger("lifeos.heart_service")

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
    "height_cm": "Height",
    "weight_kg": "Weight",
    "bmi": "Body Mass Index (BMI)",
    "systolic_bp_mmHg": "Systolic Blood Pressure",
    "diastolic_bp_mmHg": "Diastolic Blood Pressure",
    "smoking_status": "Smoking Status",
    "alcohol_status": "Alcohol Consumption",
    "physical_activity": "Physical Activity Level",
    "cholesterol_ordinal": "Cholesterol Level",
    "glucose_ordinal": "Glucose Level",
}


class HeartModelService:
    _instance: HeartModelService | None = None

    def __init__(self) -> None:
        self.artifact: dict[str, Any] | None = None
        self.pipeline: Any = None
        self.baseline_pipeline: Any = None
        self.preprocessor: Any = None
        self.xgb_model: Any = None
        self.explainer: Any = None
        self.threshold: float = 0.40
        self.feature_cols: list[str] = [
            "age_years",
            "sex",
            "height_cm",
            "weight_kg",
            "bmi",
            "systolic_bp_mmHg",
            "diastolic_bp_mmHg",
            "smoking_status",
            "alcohol_status",
            "physical_activity",
            "cholesterol_ordinal",
            "glucose_ordinal",
        ]
        self.model_name: str = "XGBoost"
        self.model_version: str = "1.0.0"
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> HeartModelService:
        if cls._instance is None:
            cls._instance = HeartModelService()
        return cls._instance

    def load_model(self) -> None:
        if self.is_loaded:
            return

        candidate_paths = [
            Path(__file__).resolve().parents[3] / "models" / "heart" / "heart_final.pkl",
            Path(__file__).resolve().parents[2] / "models" / "heart" / "heart_final.pkl",
            Path("models/heart/heart_final.pkl"),
            Path("../models/heart/heart_final.pkl"),
        ]

        model_path: Path | None = None
        for p in candidate_paths:
            if p.exists():
                model_path = p
                break

        if model_path is None:
            logger.error("Failed to locate models/heart/heart_final.pkl")
            raise FileNotFoundError("models/heart/heart_final.pkl artifact not found.")

        logger.info("Loading Heart Disease final model from: %s", model_path)
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]
        self.baseline_pipeline = self.artifact.get("baseline_pipeline") or self.pipeline
        self.threshold = float(self.artifact.get("threshold", 0.40))
        self.feature_cols = self.artifact.get("feature_cols", self.feature_cols)
        self.model_name = self.artifact.get("model_name", "XGBoost")
        self.model_version = self.artifact.get("model_version", "1.0.0")

        # Initialize SHAP TreeExplainer from baseline XGBoost model
        if hasattr(self.baseline_pipeline, "named_steps"):
            self.preprocessor = self.baseline_pipeline.named_steps.get("preprocessor")
            self.xgb_model = self.baseline_pipeline.named_steps.get("model")
            if self.xgb_model is not None:
                try:
                    booster = self.xgb_model.get_booster()
                    self.explainer = shap.TreeExplainer(booster)
                    logger.info("SHAP TreeExplainer initialized successfully.")
                except Exception as err:
                    logger.warning("Failed to initialize SHAP TreeExplainer: %s", err)

        self.is_loaded = True
        logger.info("Heart Disease model loaded successfully.")

    def get_health_status(self) -> HealthCheckResponse:
        if not self.is_loaded:
            try:
                self.load_model()
            except Exception:
                return HealthCheckResponse(
                    status="error",
                    heart_model="not_loaded",
                    model="XGBoost",
                    version="1.0.0",
                )
        return HealthCheckResponse(
            status="ok",
            heart_model="loaded",
            model=self.model_name,
            version=self.model_version,
        )

    def prepare_input_dataframe(self, req: HeartPredictionRequest) -> pd.DataFrame:
        data_dict = req.model_dump()

        # Compute BMI if missing but height and weight are provided
        if data_dict.get("bmi") is None:
            h = data_dict.get("height_cm")
            w = data_dict.get("weight_kg")
            if h is not None and w is not None and h > 0:
                data_dict["bmi"] = float(w / ((h / 100.0) ** 2))

        df = pd.DataFrame([data_dict])
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = np.nan

        return df[self.feature_cols]

    def predict(self, req: HeartPredictionRequest) -> HeartPredictionResponse:
        if not self.is_loaded:
            self.load_model()

        try:
            df = self.prepare_input_dataframe(req)
            probs = self.pipeline.predict_proba(df)[:, 1]
            risk_score = round(float(probs[0]), 4)
            prediction = int(risk_score >= self.threshold)

            if risk_score < 0.25:
                risk_level = "low"
            elif risk_score < self.threshold:
                risk_level = "moderate"
            else:
                risk_level = "high"

            return HeartPredictionResponse(
                disease="heart_disease",
                risk_score=risk_score,
                risk_level=risk_level,
                threshold=self.threshold,
                prediction=prediction,
                model=self.model_name,
                model_version=self.model_version,
            )
        except Exception as err:
            logger.error("Prediction failed: %s", err, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Heart prediction execution failed: {str(err)}")

    def explain(self, req: HeartPredictionRequest) -> HeartExplanationResponse:
        if not self.is_loaded:
            self.load_model()

        pred_resp = self.predict(req)
        df = self.prepare_input_dataframe(req)

        top_contributors: list[FeatureContribution] = []

        if self.preprocessor is not None and self.explainer is not None:
            try:
                X_trans = self.preprocessor.transform(df)
                shap_obj = self.explainer(X_trans)
                shap_vals = shap_obj.values[0]

                # Pair feature names with SHAP values
                pairs = sorted(zip(self.feature_cols, shap_vals, df.iloc[0].values), key=lambda x: abs(x[1]), reverse=True)

                for feat_name, val, raw_val in pairs[:5]:
                    contrib_val = round(float(val), 4)
                    direction = "increases_risk" if contrib_val > 0 else "decreases_risk"
                    display_name = FEATURE_NAME_MAP.get(feat_name, feat_name)

                    if direction == "increases_risk":
                        human_msg = f"{display_name} contributed significantly to increasing the model's estimated risk score."
                    else:
                        human_msg = f"{display_name} contributed to lowering the model's estimated risk score."

                    top_contributors.append(
                        FeatureContribution(
                            feature=feat_name,
                            contribution=contrib_val,
                            direction=direction,
                            human_readable=human_msg,
                        )
                    )
            except Exception as err:
                logger.warning("SHAP attribution failed: %s", err)

        return HeartExplanationResponse(
            disease="heart_disease",
            risk_score=pred_resp.risk_score,
            risk_level=pred_resp.risk_level,
            threshold=pred_resp.threshold,
            prediction=pred_resp.prediction,
            model=pred_resp.model,
            model_version=pred_resp.model_version,
            top_contributors=top_contributors,
        )


heart_service = HeartModelService.get_instance()
