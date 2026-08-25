from __future__ import annotations

from dataclasses import dataclass, field
import math


def clamp(value: float) -> float:
    return max(0.0, min(100.0, round(value, 1)))


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def normalize_yes_no(value: object | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    text = str(value).strip().lower()
    return 1.0 if text in {"1", "true", "yes", "y", "positive", "present"} else 0.0


def numeric(value: object | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class SerializedRiskModel:
    name: str
    feature_weights: dict[str, float]
    bias: float
    rationale: str
    positive_direction: str = "higher"
    feature_names: list[str] = field(default_factory=list)

    def predict_score(self, features: dict[str, object | None]) -> float:
        score = self.bias
        for feature, weight in self.feature_weights.items():
            score += numeric(features.get(feature)) * weight
        probability = sigmoid(score)
        return clamp(probability * 100.0)

    def summary(self, score: float) -> dict[str, object]:
        return {
            "model_name": self.name,
            "risk_score": score,
            "rationale": self.rationale,
        }

