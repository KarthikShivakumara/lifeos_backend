from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.health_snapshot import HealthSnapshotModel
from app.models.stress_checkin import StressCheckin
from app.schemas.stress import (
    NON_DIAGNOSTIC_DISCLAIMER,
    StressCheckinCreate,
    StressCheckinResponse,
    StressCurrentResponse,
    StressRecommendationItem,
    StressSummaryResponse,
    StressTrendPoint,
    StressTrendResponse,
)
from app.services.stress_recommendation_service import StressRecommendationService

logger = logging.getLogger("lifeos.stress_service")


class StressWellnessService:
    _instance: StressWellnessService | None = None

    @classmethod
    def get_instance(cls) -> StressWellnessService:
        if cls._instance is None:
            cls._instance = StressWellnessService()
        return cls._instance

    @staticmethod
    def calculate_sleep_strain(sleep_hours: float | None) -> float:
        """Converts sleep hours to a 0-10 strain score (higher = greater sleep strain)."""
        if sleep_hours is None:
            return 5.0  # neutral
        if sleep_hours >= 7.5:
            return 0.0
        elif sleep_hours >= 7.0:
            return 1.5
        elif sleep_hours >= 6.5:
            return 3.0
        elif sleep_hours >= 6.0:
            return 5.0
        elif sleep_hours >= 5.0:
            return 7.5
        else:
            return 10.0

    @staticmethod
    def calculate_activity_strain(activity_minutes: int | None) -> float:
        """Converts activity minutes to a 0-10 strain score (higher = lower activity / higher inactivity strain)."""
        if activity_minutes is None:
            return 5.0  # neutral
        if activity_minutes >= 45:
            return 0.0
        elif activity_minutes >= 30:
            return 2.0
        elif activity_minutes >= 20:
            return 4.0
        elif activity_minutes >= 10:
            return 7.0
        else:
            return 10.0

    @classmethod
    def calculate_stress_index(
        cls,
        perceived_stress: int,
        overwhelm: int | None = None,
        difficulty_relaxing: int | None = None,
        mood: int | None = None,
        energy: int | None = None,
        sleep_hours: float | None = None,
        activity_minutes: int | None = None,
    ) -> tuple[float, float]:
        """
        Calculates the LifeOS Stress Wellness Index (0-100) and data completeness percentage.
        Formula weights:
          - perceived_stress:     0.35 (required)
          - overwhelm:            0.20 (optional)
          - difficulty_relaxing:  0.15 (optional)
          - mood (inverted):      0.10 (optional)
          - energy (inverted):    0.10 (optional)
          - sleep_strain:         0.05 (optional lifestyle context)
          - activity_strain:      0.05 (optional lifestyle context)

        Missing components are safely normalized over available weights.
        """
        components: list[tuple[float, float]] = []  # (value_0_to_10, weight)
        user_inputs_present = 1  # perceived_stress is mandatory
        total_user_inputs = 5

        # 1. Perceived Stress (0-10)
        components.append((float(perceived_stress), 0.35))

        # 2. Overwhelm (0-10)
        if overwhelm is not None:
            components.append((float(overwhelm), 0.20))
            user_inputs_present += 1

        # 3. Difficulty Relaxing (0-10)
        if difficulty_relaxing is not None:
            components.append((float(difficulty_relaxing), 0.15))
            user_inputs_present += 1

        # 4. Mood (0=Very Low, 10=Very Good -> invert so 10 = highest strain)
        if mood is not None:
            components.append((10.0 - float(mood), 0.10))
            user_inputs_present += 1

        # 5. Energy (0=Exhausted, 10=Excellent -> invert so 10 = highest strain)
        if energy is not None:
            components.append((10.0 - float(energy), 0.10))
            user_inputs_present += 1

        # 6. Sleep Strain (0-10)
        if sleep_hours is not None:
            components.append((cls.calculate_sleep_strain(sleep_hours), 0.05))

        # 7. Activity Strain (0-10)
        if activity_minutes is not None:
            components.append((cls.calculate_activity_strain(activity_minutes), 0.05))

        # Weighted sum normalized by sum of active weights
        total_weight = sum(w for _, w in components)
        weighted_sum = sum(val * w for val, w in components)
        normalized_score = weighted_sum / total_weight if total_weight > 0 else float(perceived_stress)

        stress_index = round(max(0.0, min(100.0, normalized_score * 10.0)), 1)
        completeness = round((user_inputs_present / total_user_inputs) * 100.0, 1)

        return stress_index, completeness

    @staticmethod
    def classify_stress_level(index: float) -> str:
        if index < 25.0:
            return "low"
        elif index < 50.0:
            return "mild"
        elif index < 75.0:
            return "moderate"
        else:
            return "high"

    def record_checkin(
        self, db: Session, user_id: str, payload: StressCheckinCreate
    ) -> StressCheckinResponse:
        # Pull lifestyle context from latest assessment snapshot if available
        sleep_snapshot = None
        activity_snapshot = None
        try:
            latest_snap = (
                db.query(HealthSnapshotModel)
                .filter(HealthSnapshotModel.user_id == user_id)
                .order_by(desc(HealthSnapshotModel.created_at))
                .first()
            )
            if latest_snap and latest_snap.assessment_input_json:
                import json
                inp = json.loads(latest_snap.assessment_input_json)
                if "sleep_hours" in inp:
                    sleep_snapshot = float(inp["sleep_hours"])
                if "exercise_frequency" in inp:
                    freq = str(inp["exercise_frequency"]).lower()
                    activity_snapshot = 45 if freq in ("active", "high") else (30 if freq in ("moderate", "regular") else 10)
        except Exception as e:
            logger.debug(f"Could not retrieve snapshot lifestyle context: {e}")

        # Compute index and completeness
        stress_idx, completeness = self.calculate_stress_index(
            perceived_stress=payload.perceived_stress,
            overwhelm=payload.overwhelm,
            difficulty_relaxing=payload.difficulty_relaxing,
            mood=payload.mood,
            energy=payload.energy,
            sleep_hours=sleep_snapshot,
            activity_minutes=activity_snapshot,
        )
        stress_lvl = self.classify_stress_level(stress_idx)

        # Create immutable checkin record
        record = StressCheckin(
            user_id=user_id,
            perceived_stress=payload.perceived_stress,
            overwhelm=payload.overwhelm,
            difficulty_relaxing=payload.difficulty_relaxing,
            mood=payload.mood,
            energy=payload.energy,
            sleep_hours_snapshot=sleep_snapshot,
            activity_minutes_snapshot=activity_snapshot,
            stress_index=stress_idx,
            stress_level=stress_lvl,
            data_completeness=completeness,
            source="user_checkin",
            notes=payload.notes,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Dispatch notification if elevated stress
        try:
            from app.services.notification_service import NotificationService
            from app.models.notification import Notification
            if stress_idx >= 75.0:
                # Check for existing notification in the last 24h to avoid duplicate spam
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                existing = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user_id,
                        Notification.type == "stress_wellness",
                        Notification.created_at >= today_start,
                    )
                    .first()
                )
                if not existing:
                    NotificationService.get_instance().create_notification(
                        user_id=user_id,
                        n_type="stress_wellness",
                        title="Elevated Stress Indicator",
                        message="Your reported stress wellness index is currently elevated (High). Consider taking a recovery break today.",
                        priority="high",
                        action_url="/stress",
                        metadata={"stress_index": stress_idx, "stress_level": stress_lvl},
                        db=db,
                    )
        except Exception as err:
            logger.warning(f"Failed to dispatch stress notification: {err}")


        recs = StressRecommendationService.get_recommendation_strings(
            stress_idx, stress_lvl, sleep_snapshot, activity_snapshot
        )

        return StressCheckinResponse(
            id=record.id,
            user_id=record.user_id,
            created_at=record.created_at,
            perceived_stress=record.perceived_stress,
            overwhelm=record.overwhelm,
            difficulty_relaxing=record.difficulty_relaxing,
            mood=record.mood,
            energy=record.energy,
            sleep_hours_snapshot=record.sleep_hours_snapshot,
            activity_minutes_snapshot=record.activity_minutes_snapshot,
            stress_index=record.stress_index,
            stress_level=record.stress_level,
            data_completeness=record.data_completeness,
            is_diagnostic=False,
            recommendations=recs,
            notes=record.notes,
        )

    def get_current_stress(self, db: Session, user_id: str) -> StressCurrentResponse:
        latest = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id)
            .order_by(desc(StressCheckin.created_at))
            .first()
        )
        if not latest:
            return StressCurrentResponse(
                current_index=None,
                current_level=None,
                data_completeness=None,
                latest_checkin=None,
                rolling_7d_avg=None,
                rolling_30d_avg=None,
                trend="INSUFFICIENT_DATA",
                is_diagnostic=False,
                disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
                recommendations=[
                    "Submit a daily stress check-in to begin tracking your stress wellness trajectory."
                ],
            )

        # Rolling averages
        now = datetime.now(timezone.utc)
        since_7d = now - timedelta(days=7)
        since_30d = now - timedelta(days=30)

        checkins_7d = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id, StressCheckin.created_at >= since_7d)
            .all()
        )
        checkins_30d = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id, StressCheckin.created_at >= since_30d)
            .all()
        )

        avg_7d = (
            round(sum(c.stress_index for c in checkins_7d) / len(checkins_7d), 1)
            if checkins_7d
            else None
        )
        avg_30d = (
            round(sum(c.stress_index for c in checkins_30d) / len(checkins_30d), 1)
            if checkins_30d
            else None
        )

        # Trend calculation
        trend_resp = self.calculate_trends(db, user_id, days=7)

        recs = StressRecommendationService.get_recommendation_strings(
            latest.stress_index,
            latest.stress_level,
            latest.sleep_hours_snapshot,
            latest.activity_minutes_snapshot,
        )

        latest_resp = StressCheckinResponse(
            id=latest.id,
            user_id=latest.user_id,
            created_at=latest.created_at,
            perceived_stress=latest.perceived_stress,
            overwhelm=latest.overwhelm,
            difficulty_relaxing=latest.difficulty_relaxing,
            mood=latest.mood,
            energy=latest.energy,
            sleep_hours_snapshot=latest.sleep_hours_snapshot,
            activity_minutes_snapshot=latest.activity_minutes_snapshot,
            stress_index=latest.stress_index,
            stress_level=latest.stress_level,
            data_completeness=latest.data_completeness,
            is_diagnostic=False,
            recommendations=recs,
            notes=latest.notes,
        )

        return StressCurrentResponse(
            current_index=latest.stress_index,
            current_level=latest.stress_level,
            data_completeness=latest.data_completeness,
            latest_checkin=latest_resp,
            rolling_7d_avg=avg_7d,
            rolling_30d_avg=avg_30d,
            trend=trend_resp.trend,
            is_diagnostic=False,
            disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
            recommendations=recs,
        )

    def get_stress_history(
        self, db: Session, user_id: str, limit: int = 30
    ) -> list[StressCheckinResponse]:
        records = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id)
            .order_by(desc(StressCheckin.created_at))
            .limit(limit)
            .all()
        )
        results = []
        for r in records:
            recs = StressRecommendationService.get_recommendation_strings(
                r.stress_index, r.stress_level, r.sleep_hours_snapshot, r.activity_minutes_snapshot
            )
            results.append(
                StressCheckinResponse(
                    id=r.id,
                    user_id=r.user_id,
                    created_at=r.created_at,
                    perceived_stress=r.perceived_stress,
                    overwhelm=r.overwhelm,
                    difficulty_relaxing=r.difficulty_relaxing,
                    mood=r.mood,
                    energy=r.energy,
                    sleep_hours_snapshot=r.sleep_hours_snapshot,
                    activity_minutes_snapshot=r.activity_minutes_snapshot,
                    stress_index=r.stress_index,
                    stress_level=r.stress_level,
                    data_completeness=r.data_completeness,
                    is_diagnostic=False,
                    recommendations=recs,
                    notes=r.notes,
                )
            )
        return results

    def calculate_trends(
        self, db: Session, user_id: str, days: int = 7
    ) -> StressTrendResponse:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        records = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id, StressCheckin.created_at >= since)
            .order_by(StressCheckin.created_at.asc())
            .all()
        )

        data_points: list[StressTrendPoint] = []
        for r in records:
            data_points.append(
                StressTrendPoint(
                    date=r.created_at.strftime("%a %d"),
                    stress_index=r.stress_index,
                    stress_level=r.stress_level,
                    sleep_hours=r.sleep_hours_snapshot,
                    activity_minutes=r.activity_minutes_snapshot,
                )
            )

        if len(records) < 2:
            return StressTrendResponse(
                days_requested=days,
                data_points=data_points,
                average_index=round(records[0].stress_index, 1) if records else None,
                trend="INSUFFICIENT_DATA",
                observed_patterns=["Insufficient check-in frequency for reliable longitudinal trend evaluation."],
                is_diagnostic=False,
                disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
            )

        avg_index = round(sum(r.stress_index for r in records) / len(records), 1)

        # Trend direction (compare first half vs second half)
        mid = len(records) // 2
        first_half = records[:mid]
        second_half = records[mid:]
        avg_first = sum(r.stress_index for r in first_half) / len(first_half)
        avg_second = sum(r.stress_index for r in second_half) / len(second_half)
        diff = avg_second - avg_first

        if diff > 5.0:
            trend_dir = "INCREASING"
        elif diff < -5.0:
            trend_dir = "IMPROVING"
        else:
            trend_dir = "STABLE"

        # Observational pattern detection
        patterns: list[str] = []

        # 1. Consecutive increases
        consecutive_rises = 0
        for i in range(1, len(records)):
            if records[i].stress_index > records[i - 1].stress_index:
                consecutive_rises += 1
            else:
                consecutive_rises = 0
        if consecutive_rises >= 3:
            patterns.append(
                f"Your stress wellness indicator increased across {consecutive_rises + 1} consecutive check-ins."
            )

        # 2. Observational co-occurrence with sleep
        sleep_pairs = [(r.stress_index, r.sleep_hours_snapshot) for r in records if r.sleep_hours_snapshot is not None]
        if len(sleep_pairs) >= 2:
            high_stress_sleeps = [sl for s_idx, sl in sleep_pairs if s_idx >= 50.0]
            low_stress_sleeps = [sl for s_idx, sl in sleep_pairs if s_idx < 50.0]
            if high_stress_sleeps and low_stress_sleeps:
                if (sum(high_stress_sleeps) / len(high_stress_sleeps)) < (sum(low_stress_sleeps) / len(low_stress_sleeps)):
                    patterns.append(
                        "Elevated stress indicators occurred alongside lower recorded sleep duration during these check-ins."
                    )

        # 3. Observational co-occurrence with activity
        act_pairs = [(r.stress_index, r.activity_minutes_snapshot) for r in records if r.activity_minutes_snapshot is not None]
        if len(act_pairs) >= 2:
            high_stress_acts = [act for s_idx, act in act_pairs if s_idx >= 50.0]
            low_stress_acts = [act for s_idx, act in act_pairs if s_idx < 50.0]
            if high_stress_acts and low_stress_acts:
                if (sum(high_stress_acts) / len(high_stress_acts)) < (sum(low_stress_acts) / len(low_stress_acts)):
                    patterns.append(
                        "Higher stress ratings coincided with lower recorded physical activity minutes."
                    )

        if not patterns:
            patterns.append("Stress indicator remains stable with no acute escalation patterns detected.")

        return StressTrendResponse(
            days_requested=days,
            data_points=data_points,
            average_index=avg_index,
            trend=trend_dir,
            observed_patterns=patterns,
            is_diagnostic=False,
            disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
        )

    def get_stress_summary(self, db: Session, user_id: str) -> StressSummaryResponse:
        since_30d = datetime.now(timezone.utc) - timedelta(days=30)
        records = (
            db.query(StressCheckin)
            .filter(StressCheckin.user_id == user_id, StressCheckin.created_at >= since_30d)
            .order_by(desc(StressCheckin.created_at))
            .all()
        )
        if not records:
            return StressSummaryResponse(
                total_checkins_30d=0,
                average_index_30d=None,
                highest_index_30d=None,
                lowest_index_30d=None,
                consistency_score=0.0,
                trend="INSUFFICIENT_DATA",
                level_distribution={"low": 0, "mild": 0, "moderate": 0, "high": 0},
                is_diagnostic=False,
                disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
            )

        indices = [r.stress_index for r in records]
        unique_days = len({r.created_at.date() for r in records})
        consistency = round((unique_days / 30.0) * 100.0, 1)

        level_dist = {"low": 0, "mild": 0, "moderate": 0, "high": 0}
        for r in records:
            lvl = r.stress_level.lower()
            if lvl in level_dist:
                level_dist[lvl] += 1

        trend_res = self.calculate_trends(db, user_id, days=30)

        return StressSummaryResponse(
            total_checkins_30d=len(records),
            average_index_30d=round(sum(indices) / len(indices), 1),
            highest_index_30d=round(max(indices), 1),
            lowest_index_30d=round(min(indices), 1),
            consistency_score=consistency,
            trend=trend_res.trend,
            level_distribution=level_dist,
            is_diagnostic=False,
            disclaimer=NON_DIAGNOSTIC_DISCLAIMER,
        )


stress_wellness_service = StressWellnessService.get_instance()
