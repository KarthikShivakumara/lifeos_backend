from dataclasses import dataclass
from typing import Protocol


@dataclass
class RiskInput:
    bmi: float | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    heart_rate: int | None = None
    spo2: int | None = None
    smoking_status: str | None = None
    alcohol_use: str | None = None
    exercise_frequency: str | None = None
    diet_quality: str | None = None
    stress_level: str | None = None
    sleep_hours: float | None = None


@dataclass
class RiskOutput:
    heart_disease_risk: float
    diabetes_risk: float
    hypertension_risk: float
    overall_health_risk: float
    feature_importance: dict[str, float]
    explanation: str


class RiskModel(Protocol):
    def predict(self, data: RiskInput) -> RiskOutput: ...


class ExplanationModel(Protocol):
    def explain(self, data: RiskInput) -> dict[str, float]: ...


class CoachModel(Protocol):
    def respond(self, message: str, context: dict | None = None) -> str: ...

