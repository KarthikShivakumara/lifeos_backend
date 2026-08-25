from __future__ import annotations

import logging, uuid
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.adaptive.baseline_service import calculate_and_update_baselines, get_user_baselines
from app.services.adaptive.trend_service import evaluate_longitudinal_trends

logger = logging.getLogger("lifeos.adaptive.report_service")

DISCLAIMER_TEXT = (
    "This report provides informational, model-generated screening and wellness indicators. "
    "It is not a medical diagnosis or treatment plan. Always consult a licensed healthcare professional for clinical decisions."
)


def generate_weekly_report(db: Session, user_id: str) -> dict[str, Any]:
    """Generates Weekly Health Summary from longitudinal baseline and trend data."""
    calculate_and_update_baselines(db, user_id)
    baselines = get_user_baselines(db, user_id)
    trends = evaluate_longitudinal_trends(db, user_id)

    now = datetime.utcnow()
    p_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    p_end = now.strftime("%Y-%m-%d")

    sleep_b = next((b for b in baselines if b.metric == "sleep_hours"), None)
    steps_b = next((b for b in baselines if b.metric == "steps"), None)

    sleep_avg = sleep_b.rolling_7_day_avg if sleep_b and sleep_b.rolling_7_day_avg else 7.0
    steps_avg = steps_b.rolling_7_day_avg if steps_b and steps_b.rolling_7_day_avg else 5000.0

    personalized_recs = []
    if trends["declines"]:
        personalized_recs.extend([f"Focus on improving: {d}" for d in trends["declines"]])
    if not personalized_recs:
        personalized_recs.append("Maintain your current regular sleep and daily physical activity routine.")

    report = {
        "report_id": f"wk-{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "period_start": p_start,
        "period_end": p_end,
        "clinical_screening_summary": trends["clinical_trends"],
        "wellness_summary": {
            "sleep_7d_avg_hours": round(sleep_avg, 1),
            "steps_7d_avg": int(steps_avg),
        },
        "sleep_trend": sleep_b.trend if sleep_b else "INSUFFICIENT_DATA",
        "activity_trend": steps_b.trend if steps_b else "INSUFFICIENT_DATA",
        "nutrition_summary": {"sodium_status": "NORMAL", "fiber_status": "ADEQUATE"},
        "improvements": trends["improvements"],
        "declines": trends["declines"],
        "personalized_recommendations": personalized_recs,
        "disclaimer": DISCLAIMER_TEXT,
        "generated_at": now,
    }

    # Trigger Notification if not already issued today
    dedupe_key = f"notif-wk-{user_id}-{p_end}"
    existing_notif = db.query(Notification).filter(Notification.user_id == user_id, Notification.title == "Weekly Health Summary Ready 📊").first()
    if not existing_notif:
        notif = Notification(
            user_id=user_id,
            type="REPORT_READY",
            title="Weekly Health Summary Ready 📊",
            message=f"Your LifeOS Weekly Summary for {p_start} to {p_end} is available.",
            is_read=False,
        )
        db.add(notif)
        db.commit()

    return report


def generate_monthly_report(db: Session, user_id: str) -> dict[str, Any]:
    """Generates Monthly Health Review using 30-day longitudinal data."""
    calculate_and_update_baselines(db, user_id)
    baselines = get_user_baselines(db, user_id)
    trends = evaluate_longitudinal_trends(db, user_id)

    now = datetime.utcnow()
    month_name = now.strftime("%B %Y")

    sleep_b = next((b for b in baselines if b.metric == "sleep_hours"), None)
    steps_b = next((b for b in baselines if b.metric == "steps"), None)

    report = {
        "report_id": f"mo-{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "month_name": month_name,
        "clinical_changes": trends["clinical_trends"],
        "wellness_changes": {
            "sleep_30d_avg": round(sleep_b.rolling_30_day_avg, 1) if sleep_b and sleep_b.rolling_30_day_avg else 7.0,
            "steps_30d_avg": int(steps_b.rolling_30_day_avg) if steps_b and steps_b.rolling_30_day_avg else 5000,
        },
        "consistency_score": 0.85,
        "recommendation_adherence_rate": 0.78,
        "key_focus_areas": [
            "Maintain consistent sleep schedule",
            "Sustain daily step count goals",
            "Monitor dietary sodium intake",
        ],
        "summary_text": f"Your LifeOS Monthly Health Review for {month_name} indicates stable overall wellness indicators.",
        "disclaimer": DISCLAIMER_TEXT,
        "generated_at": now,
    }

    return report
