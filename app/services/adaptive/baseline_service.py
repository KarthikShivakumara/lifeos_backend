import json
import logging
from datetime import datetime, timedelta
from typing import Any
import numpy as np
from sqlalchemy.orm import Session

from app.models.adaptive import HealthEvent, UserBaseline
from app.models.health_assessment import HealthAssessment
from app.models.health_snapshot import HealthSnapshotModel

logger = logging.getLogger("lifeos.adaptive.baseline_service")

SUPPORTED_METRICS = [
    "weight",
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "glucose",
    "sleep_hours",
    "steps",
    "active_minutes",
    "sedentary_hours",
    "calories",
    "protein",
    "fiber",
    "sodium",
    "sugar",
]


def _extract_metric_time_series(db: Session, user_id: str, metric: str) -> list[tuple[datetime, float]]:
    """Extracts timestamped numerical observations for a given metric across snapshots, assessments, and events."""
    points: list[tuple[datetime, float]] = []

    # 1. From HealthSnapshots (JSON fields)
    snapshots = db.query(HealthSnapshotModel).filter(HealthSnapshotModel.user_id == user_id).all()
    for snap in snapshots:
        val = None
        input_data = {}
        if snap.assessment_input_json:
            try:
                input_data = json.loads(snap.assessment_input_json)
            except Exception:
                input_data = {}

        if metric == "weight":
            val = input_data.get("weight_kg") or input_data.get("weight")
        elif metric == "bmi":
            val = input_data.get("bmi")
        elif metric == "systolic_bp":
            val = input_data.get("systolic_bp") or input_data.get("systolic_bp_mmHg")
        elif metric == "diastolic_bp":
            val = input_data.get("diastolic_bp") or input_data.get("diastolic_bp_mmHg")
        elif metric == "glucose":
            val = input_data.get("blood_glucose") or input_data.get("glucose") or input_data.get("blood_glucose_level")
        elif metric == "sleep_hours":
            val = input_data.get("sleep_hours")
        elif metric == "steps":
            val = input_data.get("steps") or input_data.get("daily_steps")
        elif metric == "active_minutes":
            val = input_data.get("active_minutes")
        elif metric == "calories":
            val = input_data.get("calories") or input_data.get("calories_burned")
        if val is not None:
            points.append((snap.created_at, float(val)))

    # 2. From HealthAssessments
    assessments = db.query(HealthAssessment).filter(HealthAssessment.user_id == user_id).all()
    for assess in assessments:
        val = None
        if metric == "bmi":
            val = assess.bmi
        elif metric == "systolic_bp":
            val = assess.systolic_bp
        elif metric == "diastolic_bp":
            val = assess.diastolic_bp
        elif metric == "sleep_hours":
            val = assess.sleep_hours
        if val is not None:
            points.append((assess.created_at, float(val)))

    # 2. From HealthEvents
    events = (
        db.query(HealthEvent)
        .filter(HealthEvent.user_id == user_id)
        .order_by(HealthEvent.timestamp.asc())
        .all()
    )
    for evt in events:
        if not evt.payload or not isinstance(evt.payload, dict):
            continue
        if metric in evt.payload:
            try:
                points.append((evt.timestamp, float(evt.payload[metric])))
            except (ValueError, TypeError):
                pass

    points.sort(key=lambda x: x[0])
    return points


def calculate_metric_baseline(points: list[tuple[datetime, float]]) -> dict[str, Any]:
    if not points:
        return {
            "baseline_value": 0.0,
            "rolling_7_day_avg": None,
            "rolling_30_day_avg": None,
            "min_value": None,
            "max_value": None,
            "std_deviation": None,
            "current_deviation": None,
            "trend": "INSUFFICIENT_DATA",
            "consistency_score": 0.0,
        }

    now = datetime.utcnow()
    vals = [p[1] for p in points]
    last_val = vals[-1]

    # 7-day and 30-day windows
    p_7d = [p[1] for p in points if now - p[0] <= timedelta(days=7)]
    p_30d = [p[1] for p in points if now - p[0] <= timedelta(days=30)]

    r_7d = float(np.mean(p_7d)) if p_7d else float(np.mean(vals[-7:])) if len(vals) >= 1 else last_val
    r_30d = float(np.mean(p_30d)) if p_30d else float(np.mean(vals))

    baseline_value = float(np.mean(vals))
    min_v = float(np.min(vals))
    max_v = float(np.max(vals))
    std_dev = float(np.std(vals)) if len(vals) > 1 else 0.0
    current_dev = float(last_val - r_30d)

    # Trend calculation
    if len(vals) < 3:
        trend = "INSUFFICIENT_DATA"
    else:
        diff = r_7d - r_30d
        rel_diff = diff / (r_30d + 1e-5)
        if abs(rel_diff) < 0.03:
            trend = "STABLE"
        elif rel_diff > 0.03:
            trend = "IMPROVING"
        else:
            trend = "DECLINING"

    consistency_score = min(1.0, len(points) / 10.0)

    return {
        "baseline_value": baseline_value,
        "rolling_7_day_avg": r_7d,
        "rolling_30_day_avg": r_30d,
        "min_value": min_v,
        "max_value": max_v,
        "std_deviation": std_dev,
        "current_deviation": current_dev,
        "trend": trend,
        "consistency_score": consistency_score,
    }


def calculate_and_update_baselines(db: Session, user_id: str) -> list[UserBaseline]:
    """Recalculates rolling 7-day/30-day baselines for all 14 metrics."""
    updated_baselines: list[UserBaseline] = []

    for metric in SUPPORTED_METRICS:
        points = _extract_metric_time_series(db, user_id, metric)
        stats = calculate_metric_baseline(points)

        existing = (
            db.query(UserBaseline)
            .filter(UserBaseline.user_id == user_id, UserBaseline.metric == metric)
            .first()
        )
        if existing:
            existing.baseline_value = stats["baseline_value"]
            existing.rolling_7_day_avg = stats["rolling_7_day_avg"]
            existing.rolling_30_day_avg = stats["rolling_30_day_avg"]
            existing.min_value = stats["min_value"]
            existing.max_value = stats["max_value"]
            existing.std_deviation = stats["std_deviation"]
            existing.current_deviation = stats["current_deviation"]
            existing.trend = stats["trend"]
            existing.consistency_score = stats["consistency_score"]
            existing.last_updated = datetime.utcnow()
            ub = existing
        else:
            ub = UserBaseline(
                user_id=user_id,
                metric=metric,
                baseline_value=stats["baseline_value"],
                rolling_7_day_avg=stats["rolling_7_day_avg"],
                rolling_30_day_avg=stats["rolling_30_day_avg"],
                min_value=stats["min_value"],
                max_value=stats["max_value"],
                std_deviation=stats["std_deviation"],
                current_deviation=stats["current_deviation"],
                trend=stats["trend"],
                consistency_score=stats["consistency_score"],
            )
            db.add(ub)

        updated_baselines.append(ub)

    db.commit()
    logger.info(f"Updated baselines for user {user_id} across {len(SUPPORTED_METRICS)} metrics.")
    return updated_baselines


def get_user_baselines(db: Session, user_id: str) -> list[UserBaseline]:
    baselines = db.query(UserBaseline).filter(UserBaseline.user_id == user_id).all()
    if not baselines:
        baselines = calculate_and_update_baselines(db, user_id)
    return baselines
