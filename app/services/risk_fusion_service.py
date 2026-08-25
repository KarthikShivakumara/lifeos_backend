from __future__ import annotations

import logging
from typing import Any

from app.schemas.risk_fusion import (
    DiseaseInputItem,
    RankedDiseaseItem,
    RiskFusionRequest,
    RiskFusionResponse,
)


logger = logging.getLogger("lifeos.risk_fusion_service")

DISEASE_DISPLAY_NAMES = {
    "heart": "Heart Disease",
    "heart_disease": "Heart Disease",
    "diabetes": "Diabetes",
    "hypertension": "Hypertension",
    "obesity": "Obesity",
}

DEFAULT_DISEASE_WEIGHTS = {
    "heart": 0.25,
    "diabetes": 0.25,
    "hypertension": 0.25,
    "obesity": 0.25,
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


class RiskFusionService:
    _instance: RiskFusionService | None = None

    def __init__(self) -> None:
        self.disease_weights: dict[str, float] = dict(DEFAULT_DISEASE_WEIGHTS)

    @classmethod
    def get_instance(cls) -> RiskFusionService:
        if cls._instance is None:
            cls._instance = RiskFusionService()
        return cls._instance

    def normalize_risk(self, risk_score: float, baseline: float = 0.0) -> float:
        """Normalize risk score [0.0 - 1.0]."""
        score = max(0.0, min(1.0, float(risk_score)))
        if baseline >= 1.0:
            return score
        norm = (score - baseline) / (1.0 - baseline)
        return max(0.0, min(1.0, float(norm)))

    def fuse_risks(self, request: RiskFusionRequest) -> RiskFusionResponse:
        inputs: dict[str, DiseaseInputItem | None] = {
            "heart": request.heart,
            "diabetes": request.diabetes,
            "hypertension": request.hypertension,
            "obesity": request.obesity,
        }

        evaluated_items: list[dict[str, Any]] = []
        top_contributors_by_disease: dict[str, list[dict[str, Any]]] = {}
        missing_diseases: list[str] = []

        total_weighted_norm_risk = 0.0
        total_applied_weight = 0.0

        for key, item in inputs.items():
            if item is None:
                missing_diseases.append(key)
                continue

            disease_key = item.disease.lower()
            if disease_key not in DISEASE_DISPLAY_NAMES:
                disease_key = key

            disp_name = DISEASE_DISPLAY_NAMES.get(disease_key, disease_key.title())

            norm_risk = self.normalize_risk(item.risk_score)
            risk_pct = round(norm_risk * 100.0, 2)
            r_level = classify_risk_level(norm_risk)

            weight = self.disease_weights.get(key, 0.25)
            total_weighted_norm_risk += norm_risk * weight
            total_applied_weight += weight

            eval_dict = {
                "disease": key,
                "display_name": disp_name,
                "risk_score": round(float(item.risk_score), 4),
                "normalized_risk": round(norm_risk, 4),
                "risk_percentage": risk_pct,
                "risk_level": r_level,
                "threshold": round(float(item.threshold), 2),
                "model": item.model,
                "prediction": item.prediction,
            }
            evaluated_items.append(eval_dict)

            if item.top_contributors:
                top_contributors_by_disease[key] = item.top_contributors

        if not evaluated_items:
            # Fallback if all disease inputs were empty/null
            return RiskFusionResponse(
                overall_risk_score=0.0,
                overall_risk_percentage=0.0,
                overall_risk_level="low",
                overall_health_score=100,
                top_priority_disease="none",
                top_priority_display_name="None",
                top_priority_score=0.0,
                disease_ranking=[],
                high_risk_diseases=[],
                very_high_risk_diseases=[],
                multiple_high_risk=False,
                multiple_very_high_risk=False,
                top_contributors_by_disease={},
                available_diseases_count=0,
                missing_diseases=["heart", "diabetes", "hypertension", "obesity"],
            )

        # Calculate Overall Health Risk Score
        overall_risk_score = round(total_weighted_norm_risk / total_applied_weight, 4) if total_applied_weight > 0 else 0.0
        overall_risk_pct = round(overall_risk_score * 100.0, 2)
        overall_risk_level = classify_risk_level(overall_risk_score)
        overall_health_score = int(round(100.0 - overall_risk_pct))

        # Rank diseases by normalized risk descending
        sorted_evals = sorted(evaluated_items, key=lambda x: x["normalized_risk"], reverse=True)

        ranked_items: list[RankedDiseaseItem] = []
        high_risk_diseases: list[str] = []
        very_high_risk_diseases: list[str] = []

        for idx, eval_item in enumerate(sorted_evals, start=1):
            r_level = eval_item["risk_level"]
            d_name = eval_item["disease"]

            if r_level in ["high", "very_high"]:
                high_risk_diseases.append(d_name)
            if r_level == "very_high":
                very_high_risk_diseases.append(d_name)

            ranked_items.append(
                RankedDiseaseItem(
                    rank=idx,
                    disease=d_name,
                    display_name=eval_item["display_name"],
                    risk_score=eval_item["risk_score"],
                    normalized_risk=eval_item["normalized_risk"],
                    risk_percentage=eval_item["risk_percentage"],
                    risk_level=r_level,
                    threshold=eval_item["threshold"],
                    model=eval_item["model"],
                )
            )

        top_priority = ranked_items[0]

        return RiskFusionResponse(
            overall_risk_score=overall_risk_score,
            overall_risk_percentage=overall_risk_pct,
            overall_risk_level=overall_risk_level,
            overall_health_score=overall_health_score,
            top_priority_disease=top_priority.disease,
            top_priority_display_name=top_priority.display_name,
            top_priority_score=top_priority.risk_score,
            disease_ranking=ranked_items,
            high_risk_diseases=high_risk_diseases,
            very_high_risk_diseases=very_high_risk_diseases,
            multiple_high_risk=len(high_risk_diseases) >= 2,
            multiple_very_high_risk=len(very_high_risk_diseases) >= 2,
            top_contributors_by_disease=top_contributors_by_disease,
            available_diseases_count=len(evaluated_items),
            missing_diseases=missing_diseases,
        )


risk_fusion_service = RiskFusionService.get_instance()
