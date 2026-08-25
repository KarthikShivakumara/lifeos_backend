from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CKDPredictionRequest(BaseModel):
    age: float = Field(..., ge=1.0, le=120.0, description="Age in years")
    bp: float = Field(..., ge=40.0, le=220.0, description="Blood pressure in mmHg")
    sg: float = Field(..., ge=1.000, le=1.040, description="Specific Gravity (1.005 - 1.030)")
    al: float = Field(..., ge=0.0, le=5.0, description="Albumin (0 - 5)")
    su: float = Field(..., ge=0.0, le=5.0, description="Sugar (0 - 5)")
    bgr: float = Field(..., ge=30.0, le=600.0, description="Blood Glucose Random in mg/dL")
    bu: float = Field(..., ge=1.0, le=400.0, description="Blood Urea in mg/dL")
    sc: float = Field(..., ge=0.1, le=30.0, description="Serum Creatinine in mg/dL")
    sod: float = Field(..., ge=80.0, le=190.0, description="Sodium in mEq/L")
    pot: float = Field(..., ge=1.0, le=15.0, description="Potassium in mEq/L")
    hemo: float = Field(..., ge=2.0, le=25.0, description="Hemoglobin in g")
    pcv: float = Field(..., ge=10.0, le=70.0, description="Packed Cell Volume")
    wc: float = Field(..., ge=1000.0, le=40000.0, description="White Blood Cell Count")
    rc: float = Field(..., ge=1.0, le=10.0, description="Red Blood Cell Count")
    rbc: str = Field(..., description="Red Blood Cells: 'normal' or 'abnormal'")
    pc: str = Field(..., description="Pus Cell: 'normal' or 'abnormal'")
    pcc: str = Field(..., description="Pus Cell Clumps: 'present' or 'notpresent'")
    ba: str = Field(..., description="Bacteria: 'present' or 'notpresent'")
    htn: str = Field(..., description="Hypertension history: 'yes' or 'no'")
    dm: str = Field(..., description="Diabetes mellitus history: 'yes' or 'no'")
    cad: str = Field(..., description="Coronary Artery Disease: 'yes' or 'no'")
    appet: str = Field(..., description="Appetite: 'good' or 'poor'")
    pe: str = Field(..., description="Pedal Edema: 'yes' or 'no'")
    ane: str = Field(..., description="Anemia: 'yes' or 'no'")

    @field_validator("rbc", "pc")
    @classmethod
    def validate_normal_abnormal(cls, v: str) -> str:
        if v not in ("normal", "abnormal"):
            raise ValueError("Value must be 'normal' or 'abnormal'")
        return v

    @field_validator("pcc", "ba")
    @classmethod
    def validate_present_notpresent(cls, v: str) -> str:
        if v not in ("present", "notpresent"):
            raise ValueError("Value must be 'present' or 'notpresent'")
        return v

    @field_validator("htn", "dm", "cad", "pe", "ane")
    @classmethod
    def validate_yes_no(cls, v: str) -> str:
        if v not in ("yes", "no"):
            raise ValueError("Value must be 'yes' or 'no'")
        return v

    @field_validator("appet")
    @classmethod
    def validate_appet(cls, v: str) -> str:
        if v not in ("good", "poor"):
            raise ValueError("appet must be 'good' or 'poor'")
        return v


class CKDPredictionResponse(BaseModel):
    disease: Literal["ckd"] = "ckd"
    risk_score: float = Field(..., description="Estimated Calibrated Risk Score (0.0 to 1.0)")
    risk_level: Literal["low", "moderate", "high", "very_high"] = Field(..., description="Risk level category")
    threshold: float = Field(0.33, description="Operating threshold selected from validation set")
    prediction: int = Field(..., description="Binary risk prediction (0 = Low/Moderate Risk, 1 = High Risk)")
    model: str = "XGBoost"
    model_version: str = "1.0.0"


class FeatureContribution(BaseModel):
    feature: str = Field(..., description="Feature column name")
    contribution: float = Field(..., description="SHAP feature attribution value")
    direction: Literal["increases_risk", "decreases_risk"] = Field(..., description="Impact direction on risk prediction")
    human_readable: str = Field(..., description="Human-readable explanation of feature impact")


class CKDExplanationResponse(BaseModel):
    disease: Literal["ckd"] = "ckd"
    base_value: float = Field(..., description="SHAP baseline expectation score")
    top_contributions: list[FeatureContribution] = Field(..., description="Ranked feature attributions")
    explanation_summary: str = Field(..., description="Summary explanation string")
