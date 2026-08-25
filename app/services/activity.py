from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.schemas.activity import ActivityEngineInput, ActivitySignal

logger = logging.getLogger("lifeos.activity_engine")


def log_activity(
    db: Session,
    user_id: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: str | None = None,
) -> ActivityLog:
    log_entry = ActivityLog(
        user_id=str(user_id),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


class ActivityEngine:
    _instance: ActivityEngine | None = None

    @classmethod
    def get_instance(cls) -> ActivityEngine:
        if cls._instance is None:
            cls._instance = ActivityEngine()
        return cls._instance

    def evaluate_activity(self, data: ActivityEngineInput) -> ActivitySignal:
        steps = data.daily_steps
        mvpa = data.very_active_minutes + data.fairly_active_minutes
        sedentary_hrs = round(data.sedentary_minutes / 60.0, 1)

        # 1. Step Score (0-50 pts based on 10,000 steps target)
        step_pts = min(50.0, (steps / 10000.0) * 50.0)

        # 2. Active Minutes Score (0-30 pts based on 30 mins MVPA target)
        mvpa_pts = min(30.0, (mvpa / 30.0) * 30.0)

        # 3. Sedentary Penalty (0-20 pts deduction if sedentary > 8 hours)
        sedentary_pts = 20.0
        if sedentary_hrs > 8.0:
            excess_hrs = sedentary_hrs - 8.0
            sedentary_pts = max(0.0, 20.0 - (excess_hrs * 2.5))

        activity_score = round(min(100.0, step_pts + mvpa_pts + sedentary_pts), 1)

        # Activity Level Classification
        if steps >= 7500 or mvpa >= 30:
            activity_level = "optimal"
        elif steps >= 5000 or mvpa >= 15:
            activity_level = "moderate"
        else:
            activity_level = "low"

        # Sedentary Risk Classification
        if sedentary_hrs >= 10.0:
            sedentary_risk = "elevated"
        elif sedentary_hrs >= 8.0:
            sedentary_risk = "moderate"
        else:
            sedentary_risk = "low"

        # Trend Calculation
        history = data.historical_steps
        if len(history) >= 3:
            recent_avg = sum(history[-3:]) / 3.0
            older_avg = sum(history[:-3]) / len(history[:-3]) if len(history) > 3 else history[0]
            if recent_avg > older_avg * 1.05:
                trend = "IMPROVING"
            elif recent_avg < older_avg * 0.95:
                trend = "DECLINING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        # Consistency
        if history:
            active_days = sum(1 for s in history if s >= 5000)
            consistency_pct = round((active_days / len(history)) * 100.0, 1)
        else:
            consistency_pct = 100.0 if steps >= 5000 else 0.0

        # Recommendation Triggers
        triggers = []
        if steps < 5000:
            triggers.append("low_daily_step_count")
        if sedentary_hrs >= 10.0:
            triggers.append("elevated_sedentary_time")
        if trend == "DECLINING":
            triggers.append("declining_activity_trend")
        if mvpa < 15:
            triggers.append("insufficient_aerobic_activity")

        return ActivitySignal(
            domain="activity",
            activity_score=activity_score,
            activity_level=activity_level,
            sedentary_risk=sedentary_risk,
            weekly_trend=trend,
            exercise_consistency_pct=consistency_pct,
            daily_steps=steps,
            active_minutes=mvpa,
            sedentary_hours=sedentary_hrs,
            source="deterministic_activity_engine",
            recommendation_triggers=triggers,
        )

    def to_wellness_signal(self, data: ActivityEngineInput) -> Any:
        from app.schemas.wellness import WellnessFactor, WellnessSignal

        sig = self.evaluate_activity(data)
        normalized_score = round(sig.activity_score / 100.0, 2)

        # Map to WellnessSignal level ('low', 'moderate', 'elevated', 'optimal')
        if sig.activity_level == "optimal" and sig.sedentary_risk == "low":
            w_level = "optimal"
        elif sig.activity_level == "low" or sig.sedentary_risk == "elevated":
            w_level = "elevated"
        elif sig.activity_level == "moderate":
            w_level = "moderate"
        else:
            w_level = "low"

        factors = [
            WellnessFactor(
                feature=tr,
                contribution=0.25,
                direction="increases_risk" if "low" in tr or "elevated" in tr or "declining" in tr else "decreases_risk",
                human_readable=tr.replace("_", " ").title(),
            )
            for tr in sig.recommendation_triggers
        ]

        return WellnessSignal(
            domain="activity",
            score=normalized_score,
            level=w_level,
            status=f"activity_wellness_{sig.activity_level}",
            top_factors=factors,
            source="deterministic_activity_engine",
            metadata={
                "activity_score": sig.activity_score,
                "activity_level": sig.activity_level,
                "sedentary_risk": sig.sedentary_risk,
                "daily_steps": sig.daily_steps,
                "active_minutes": sig.active_minutes,
                "sedentary_hours": sig.sedentary_hours,
                "weekly_trend": sig.weekly_trend,
                "exercise_consistency_pct": sig.exercise_consistency_pct,
            },
        )


activity_engine = ActivityEngine.get_instance()
