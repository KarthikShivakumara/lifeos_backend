from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.services.adaptive.baseline_service import calculate_and_update_baselines, get_user_baselines

logger = logging.getLogger("lifeos.adaptive.trend_service")


def evaluate_longitudinal_trends(db: Session, user_id: str) -> dict[str, Any]:
    """Synthesizes metric trends across clinical and wellness categories."""
    baselines = get_user_baselines(db, user_id)
    baseline_map = {b.metric: b for b in baselines}

    clinical_trends = {
        "systolic_bp": baseline_map.get("systolic_bp").trend if baseline_map.get("systolic_bp") else "INSUFFICIENT_DATA",
        "diastolic_bp": baseline_map.get("diastolic_bp").trend if baseline_map.get("diastolic_bp") else "INSUFFICIENT_DATA",
        "glucose": baseline_map.get("glucose").trend if baseline_map.get("glucose") else "INSUFFICIENT_DATA",
        "bmi": baseline_map.get("bmi").trend if baseline_map.get("bmi") else "INSUFFICIENT_DATA",
    }

    wellness_trends = {
        "sleep": baseline_map.get("sleep_hours").trend if baseline_map.get("sleep_hours") else "INSUFFICIENT_DATA",
        "activity": baseline_map.get("steps").trend if baseline_map.get("steps") else "INSUFFICIENT_DATA",
        "sodium": baseline_map.get("sodium").trend if baseline_map.get("sodium") else "INSUFFICIENT_DATA",
    }

    improvements: list[str] = []
    declines: list[str] = []

    for metric, b in baseline_map.items():
        if b.trend == "IMPROVING":
            improvements.append(f"{metric.replace('_', ' ').title()} is showing positive improvement.")
        elif b.trend == "DECLINING":
            declines.append(f"{metric.replace('_', ' ').title()} is currently declining compared to baseline.")

    return {
        "user_id": user_id,
        "clinical_trends": clinical_trends,
        "wellness_trends": wellness_trends,
        "improvements": improvements,
        "declines": declines,
        "total_metrics_evaluated": len(baselines),
    }


def get_personalized_recommendation_modifiers(db: Session, user_id: str) -> list[str]:
    """Generates personalized priority boosts based on baseline trend analysis."""
    baselines = get_user_baselines(db, user_id)
    modifiers: list[str] = []

    sleep_b = next((b for b in baselines if b.metric == "sleep_hours"), None)
    if sleep_b and sleep_b.rolling_7_day_avg and sleep_b.rolling_30_day_avg:
        if sleep_b.rolling_7_day_avg < sleep_b.rolling_30_day_avg and sleep_b.trend == "DECLINING":
            modifiers.append(
                f"Your average sleep duration has decreased from {sleep_b.rolling_30_day_avg:.1f}h to {sleep_b.rolling_7_day_avg:.1f}h over the recent period."
            )

    steps_b = next((b for b in baselines if b.metric == "steps"), None)
    if steps_b and steps_b.rolling_7_day_avg and steps_b.rolling_30_day_avg:
        if steps_b.rolling_7_day_avg > steps_b.rolling_30_day_avg:
            modifiers.append(
                f"Your daily physical activity has improved, averaging {int(steps_b.rolling_7_day_avg)} steps compared to your 30-day baseline of {int(steps_b.rolling_30_day_avg)} steps."
            )

    return modifiers
