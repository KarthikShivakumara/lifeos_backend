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

from app.schemas.ckd import (
    CKDExplanationResponse,
    CKDPredictionRequest,
    CKDPredictionResponse,
    FeatureContribution,
)

logger = logging.getLogger("lifeos.ckd_service")

# Apply monkey-patch to SHAP UBJSON decoder for XGBoost compatibility
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
    "age": "Age",
    "bp": "Blood Pressure",
    "sg": "Specific Gravity",
    "al": "Albumin Level",
    "su": "Sugar Level",
    "bgr": "Blood Glucose Random",
    "bu": "Blood Urea",
    "sc": "Serum Creatinine",
    "sod": "Sodium Level",
    "pot": "Potassium Level",
    "hemo": "Hemoglobin Level",
    "pcv": "Packed Cell Volume",
    "wc": "White Blood Cell Count",
    "rc": "Red Blood Cell Count",
    "rbc": "Red Blood Cells",
    "pc": "Pus Cell",
    "pcc": "Pus Cell Clumps",
    "ba": "Bacteria Presence",
    "htn": "Hypertension History",
    "dm": "Diabetes Mellitus History",
    "cad": "Coronary Artery Disease History",
    "appet": "Appetite Assessment",
    "pe": "Pedal Edema",
    "ane": "Anemia Presence",
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


class CKDModelService:
    _instance: CKDModelService | None = None

    def __init__(self) -> None:
        self.model_loaded = False
        self.artifact: dict[str, Any] = {}
        self.preprocessor = None
        self.model = None
        self.calibrated_model = None
        self.explainer = None
        self.operating_threshold = 0.33
        self._load_artifact()

    @classmethod
    def get_instance(cls) -> CKDModelService:
        if cls._instance is None:
            cls._instance = CKDModelService()
        return cls._instance

    def _load_artifact(self) -> None:
        root_dir = Path(__file__).resolve().parents[3]
        model_path = root_dir / "models" / "ckd" / "ckd_final.pkl"

        if not model_path.exists():
            logger.warning(f"CKD model artifact not found at {model_path}")
            return

        try:
            self.artifact = joblib.load(model_path)
            self.preprocessor = self.artifact.get("preprocessor")
            self.model = self.artifact.get("model")
            self.calibrated_model = self.artifact.get("calibrated_model")
            self.operating_threshold = float(self.artifact.get("operating_threshold", 0.33))

            if self.model is not None:
                self.explainer = shap.TreeExplainer(self.model)
                self.model_loaded = True
                logger.info(f"CKD model artifact loaded successfully from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load CKD model artifact: {e}")

    def predict(self, request: CKDPredictionRequest) -> CKDPredictionResponse:
        if not self.model_loaded or self.calibrated_model is None or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="CKD prediction service is currently unavailable.")

        try:
            input_df = pd.DataFrame([{
                "age": request.age,
                "bp": request.bp,
                "sg": request.sg,
                "al": request.al,
                "su": request.su,
                "bgr": request.bgr,
                "bu": request.bu,
                "sc": request.sc,
                "sod": request.sod,
                "pot": request.pot,
                "hemo": request.hemo,
                "pcv": request.pcv,
                "wc": request.wc,
                "rc": request.rc,
                "rbc": request.rbc,
                "pc": request.pc,
                "pcc": request.pcc,
                "ba": request.ba,
                "htn": request.htn,
                "dm": request.dm,
                "cad": request.cad,
                "appet": request.appet,
                "pe": request.pe,
                "ane": request.ane,
            }])

            X_trans = self.preprocessor.transform(input_df)
            cal_probs = self.calibrated_model.predict_proba(X_trans)[0]
            prob = float(cal_probs[1])

            risk_level = classify_risk_level(prob)
            prediction = 1 if prob >= self.operating_threshold else 0

            return CKDPredictionResponse(
                disease="ckd",
                risk_score=round(prob, 4),
                risk_level=risk_level,
                threshold=round(self.operating_threshold, 4),
                prediction=prediction,
                model="XGBoost",
                model_version="1.0.0",
            )
        except Exception as e:
            logger.error(f"Error during CKD prediction: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    def explain(self, request: CKDPredictionRequest) -> CKDExplanationResponse:
        if not self.model_loaded or self.explainer is None or self.preprocessor is None:
            raise HTTPException(status_code=503, detail="CKD explanation service is currently unavailable.")

        try:
            input_df = pd.DataFrame([{
                "age": request.age,
                "bp": request.bp,
                "sg": request.sg,
                "al": request.al,
                "su": request.su,
                "bgr": request.bgr,
                "bu": request.bu,
                "sc": request.sc,
                "sod": request.sod,
                "pot": request.pot,
                "hemo": request.hemo,
                "pcv": request.pcv,
                "wc": request.wc,
                "rc": request.rc,
                "rbc": request.rbc,
                "pc": request.pc,
                "pcc": request.pcc,
                "ba": request.ba,
                "htn": request.htn,
                "dm": request.dm,
                "cad": request.cad,
                "appet": request.appet,
                "pe": request.pe,
                "ane": request.ane,
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
            summary = "CKD risk attributions driven by: " + "; ".join(top_3) + "."

            return CKDExplanationResponse(
                disease="ckd",
                base_value=round(bv, 4),
                top_contributions=contributions,
                explanation_summary=summary,
            )
        except Exception as e:
            logger.error(f"Error during CKD explanation: {e}")
            raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")
