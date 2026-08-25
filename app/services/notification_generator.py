from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.services.history_service import history_service
from app.services.notification_rules import rule_engine
from app.services.notification_service import notification_service

logger = logging.getLogger("lifeos.notification_generator")


class NotificationGenerator:
    _instance: NotificationGenerator | None = None

    @classmethod
    def get_instance(cls) -> NotificationGenerator:
        if cls._instance is None:
            cls._instance = NotificationGenerator()
        return cls._instance

    def _is_duplicate(
        self,
        user_id: str,
        n_type: str,
        dedupe_key: str,
        db: Session | None = None,
    ) -> bool:
        if db is not None:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.type == n_type,
                    Notification.metadata_json.like(f"%{dedupe_key}%"),
                )
                .first()
            )
            return existing is not None
        else:
            for item in notification_service._in_memory_notifications:
                if item["user_id"] == user_id and item["type"] == n_type:
                    meta = item.get("metadata", {})
                    if dedupe_key in str(meta):
                        return True
            return False

    def check_30_day_assessment_reminder(self, user_id: str, db: Session | None = None) -> NotificationResponse | None:
        try:
            snaps = history_service.get_history(user_id=user_id, db=db).snapshots
            if not snaps:
                return None

            latest_ts_str = snaps[0].timestamp
            try:
                latest_dt = datetime.fromisoformat(latest_ts_str.replace("Z", "+00:00"))
            except Exception:
                return None

            now_dt = datetime.now(timezone.utc)
            days_diff = (now_dt - latest_dt).days

            if days_diff >= 30:
                dedupe_key = f"reminder-{now_dt.strftime('%Y-%m')}"
                if not self._is_duplicate(user_id, "assessment_reminder", dedupe_key, db=db):
                    return notification_service.create_notification(
                        user_id=user_id,
                        n_type="assessment_reminder",
                        title="Time for a Health Check-In",
                        message="It has been around 30 days since your last LifeOS assessment. Complete another assessment to track changes over time.",
                        priority="moderate",
                        action_url="/assessment",
                        metadata={"days_since_last": days_diff, "dedupe_key": dedupe_key},
                        db=db,
                    )
        except Exception as err:
            logger.warning("Failed evaluating 30-day assessment reminder: %s", err)
        return None

    def generate_for_user(
        self,
        user_id: str,
        snapshot_id: str | None = None,
        db: Session | None = None,
    ) -> list[NotificationResponse]:
        created_notifications: list[NotificationResponse] = []

        try:
            snaps = history_service.get_history(user_id=user_id, db=db).snapshots
            if not snaps:
                rem = self.check_30_day_assessment_reminder(user_id=user_id, db=db)
                if rem:
                    created_notifications.append(rem)
                return created_notifications

            latest_snap = snaps[0]
            current_snap_id = snapshot_id or latest_snap.id

            rf = latest_snap.risk_fusion or {}
            dis = latest_snap.disease_results or {}
            input_data = latest_snap.assessment_input or {}
            recs = latest_snap.recommendations or []

            # 1. Evaluate Overall Risk Rule
            rule_ov = rule_engine.evaluate_overall_risk_rule(rf)
            dedupe_ov = f"ov-{current_snap_id}"
            if rule_ov and not self._is_duplicate(user_id, rule_ov["type"], dedupe_ov, db=db):
                meta = rule_ov.get("metadata", {})
                meta["snapshot_id"] = current_snap_id
                meta["dedupe_key"] = dedupe_ov
                n = notification_service.create_notification(
                    user_id=user_id,
                    n_type=rule_ov["type"],
                    title=rule_ov["title"],
                    message=rule_ov["message"],
                    priority=rule_ov["priority"],
                    action_url=rule_ov["action_url"],
                    metadata=meta,
                    db=db,
                )
                created_notifications.append(n)

            # 2. Evaluate Disease High Risk Consolidation Rule
            rule_dis = rule_engine.evaluate_disease_rules(dis)
            dedupe_dis = f"dis-{current_snap_id}"
            if rule_dis and not self._is_duplicate(user_id, rule_dis["type"], dedupe_dis, db=db):
                meta = rule_dis.get("metadata", {})
                meta["snapshot_id"] = current_snap_id
                meta["dedupe_key"] = dedupe_dis
                n = notification_service.create_notification(
                    user_id=user_id,
                    n_type=rule_dis["type"],
                    title=rule_dis["title"],
                    message=rule_dis["message"],
                    priority=rule_dis["priority"],
                    action_url=rule_dis["action_url"],
                    metadata=meta,
                    db=db,
                )
                created_notifications.append(n)

            # 3. Evaluate Biomarker Alerts Rule
            rule_bio = rule_engine.evaluate_biomarker_rules(input_data)
            dedupe_bio = f"bio-{current_snap_id}"
            if rule_bio and not self._is_duplicate(user_id, rule_bio["type"], dedupe_bio, db=db):
                meta = rule_bio.get("metadata", {})
                meta["snapshot_id"] = current_snap_id
                meta["dedupe_key"] = dedupe_bio
                n = notification_service.create_notification(
                    user_id=user_id,
                    n_type=rule_bio["type"],
                    title=rule_bio["title"],
                    message=rule_bio["message"],
                    priority=rule_bio["priority"],
                    action_url=rule_bio["action_url"],
                    metadata=meta,
                    db=db,
                )
                created_notifications.append(n)

            # 4. Evaluate Recommendation Reminders Rule
            rule_rec = rule_engine.evaluate_recommendation_rule(recs)
            dedupe_rec = f"rec-{current_snap_id}"
            if rule_rec and not self._is_duplicate(user_id, rule_rec["type"], dedupe_rec, db=db):
                meta = rule_rec.get("metadata", {})
                meta["snapshot_id"] = current_snap_id
                meta["dedupe_key"] = dedupe_rec
                n = notification_service.create_notification(
                    user_id=user_id,
                    n_type=rule_rec["type"],
                    title=rule_rec["title"],
                    message=rule_rec["message"],
                    priority=rule_rec["priority"],
                    action_url=rule_rec["action_url"],
                    metadata=meta,
                    db=db,
                )
                created_notifications.append(n)

            # 4.5. Evaluate Wellness Alerts Rule
            rule_well = rule_engine.evaluate_wellness_rules(dis)
            dedupe_well = f"well-{current_snap_id}"
            if rule_well and not self._is_duplicate(user_id, rule_well["type"], dedupe_well, db=db):
                meta = rule_well.get("metadata", {})
                meta["snapshot_id"] = current_snap_id
                meta["dedupe_key"] = dedupe_well
                n = notification_service.create_notification(
                    user_id=user_id,
                    n_type=rule_well["type"],
                    title=rule_well["title"],
                    message=rule_well["message"],
                    priority=rule_well["priority"],
                    action_url=rule_well["action_url"],
                    metadata=meta,
                    db=db,
                )
                created_notifications.append(n)

            # 5. Evaluate Trend Alerts Rule (if >= 2 snapshots exist)
            if len(snaps) >= 2:
                trends = history_service.calculate_trends(snaps)
                rule_tr = rule_engine.evaluate_trend_rule(trends)
                dedupe_tr = f"trend-{current_snap_id}"
                if rule_tr and not self._is_duplicate(user_id, rule_tr["type"], dedupe_tr, db=db):
                    meta = rule_tr.get("metadata", {})
                    meta["snapshot_id"] = current_snap_id
                    meta["dedupe_key"] = dedupe_tr
                    n = notification_service.create_notification(
                        user_id=user_id,
                        n_type=rule_tr["type"],
                        title=rule_tr["title"],
                        message=rule_tr["message"],
                        priority=rule_tr["priority"],
                        action_url=rule_tr["action_url"],
                        metadata=meta,
                        db=db,
                    )
                    created_notifications.append(n)

            # 6. Check 30-day assessment reminder
            rem = self.check_30_day_assessment_reminder(user_id=user_id, db=db)
            if rem:
                created_notifications.append(rem)

        except Exception as err:
            logger.error("Error during notification generation for user %s: %s", user_id, err)

        return created_notifications


notification_generator = NotificationGenerator.get_instance()
