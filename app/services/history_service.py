from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.health_snapshot import HealthSnapshotModel
from app.schemas.history import (
    HealthHistoryResponse,
    HealthSnapshot,
    HealthTrendPoint,
    HealthTrendSummary,
    MetricTrendItem,
    RiskTrendSummary,
    TrendDirection,
)

logger = logging.getLogger("lifeos.history_service")

DEFAULT_STABILITY_TOLERANCE = 0.03


class HistoryService:
    _instance: HistoryService | None = None

    def __init__(self) -> None:
        self._snapshots: dict[str, HealthSnapshot] = {}
        self.max_snapshots: int = 100
        self.stability_tolerance: float = DEFAULT_STABILITY_TOLERANCE

    @classmethod
    def get_instance(cls) -> HistoryService:
        if cls._instance is None:
            cls._instance = HistoryService()
        return cls._instance

    def create_snapshot(
        self,
        assessment_input: dict[str, Any],
        disease_results: dict[str, Any],
        risk_fusion: dict[str, Any] | None = None,
        recommendations: list[dict[str, Any]] | None = None,
        custom_id: str | None = None,
        custom_timestamp: str | None = None,
        user_id: str | None = None,
        db: Session | None = None,
    ) -> HealthSnapshot:
        snap_id = custom_id or f"snap-{uuid.uuid4().hex[:10]}"
        timestamp = custom_timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()

        snapshot = HealthSnapshot(
            id=snap_id,
            timestamp=timestamp,
            assessment_input=assessment_input or {},
            disease_results=disease_results or {},
            risk_fusion=risk_fusion,
            recommendations=recommendations or [],
        )
        setattr(snapshot, "_user_id", user_id)

        if db is not None:
            try:
                db_model = HealthSnapshotModel(
                    id=snap_id,
                    user_id=user_id,
                    timestamp=timestamp,
                    assessment_input_json=json.dumps(assessment_input or {}),
                    disease_results_json=json.dumps(disease_results or {}),
                    risk_fusion_json=json.dumps(risk_fusion) if risk_fusion else None,
                    recommendations_json=json.dumps(recommendations) if recommendations else None,
                )
                db.add(db_model)
                db.commit()
            except Exception as err:
                logger.warning("Database snapshot persistence warning: %s", err)
                db.rollback()

        # In-memory storage update
        self._snapshots[snap_id] = snapshot

        # Keep memory bounded
        if len(self._snapshots) > self.max_snapshots:
            sorted_keys = sorted(
                self._snapshots.keys(),
                key=lambda k: self._snapshots[k].timestamp,
                reverse=True,
            )
            for k in sorted_keys[self.max_snapshots:]:
                del self._snapshots[k]

        return snapshot

    def get_history(self, user_id: str | None = None, db: Session | None = None) -> HealthHistoryResponse:
        if db is not None and user_id is not None:
            db_snaps = (
                db.query(HealthSnapshotModel)
                .filter(HealthSnapshotModel.user_id == user_id)
                .order_by(HealthSnapshotModel.created_at.desc())
                .all()
            )
            snapshots: list[HealthSnapshot] = []
            for s in db_snaps:
                snapshots.append(
                    HealthSnapshot(
                        id=s.id,
                        timestamp=s.timestamp,
                        assessment_input=json.loads(s.assessment_input_json) if s.assessment_input_json else {},
                        disease_results=json.loads(s.disease_results_json) if s.disease_results_json else {},
                        risk_fusion=json.loads(s.risk_fusion_json) if s.risk_fusion_json else None,
                        recommendations=json.loads(s.recommendations_json) if s.recommendations_json else [],
                    )
                )
            return HealthHistoryResponse(snapshots=snapshots, total_count=len(snapshots))

        # Memory fallback
        sorted_snaps = sorted(
            self._snapshots.values(),
            key=lambda s: s.timestamp,
            reverse=True,
        )
        return HealthHistoryResponse(snapshots=sorted_snaps, total_count=len(sorted_snaps))

    def get_snapshot(self, snapshot_id: str, user_id: str | None = None, db: Session | None = None) -> HealthSnapshot | None:
        if db is not None:
            query = db.query(HealthSnapshotModel).filter(HealthSnapshotModel.id == snapshot_id)
            if user_id is not None:
                query = query.filter(HealthSnapshotModel.user_id == user_id)
            s = query.first()
            if s:
                return HealthSnapshot(
                    id=s.id,
                    timestamp=s.timestamp,
                    assessment_input=json.loads(s.assessment_input_json) if s.assessment_input_json else {},
                    disease_results=json.loads(s.disease_results_json) if s.disease_results_json else {},
                    risk_fusion=json.loads(s.risk_fusion_json) if s.risk_fusion_json else None,
                    recommendations=json.loads(s.recommendations_json) if s.recommendations_json else [],
                )

        snap = self._snapshots.get(snapshot_id)
        if snap is not None and user_id is not None:
            # Check if user_id stored on memory model matches
            snap_user = getattr(snap, "_user_id", None)
            if snap_user is not None and snap_user != user_id:
                return None
        return snap

    def delete_snapshot(self, snapshot_id: str, user_id: str | None = None, db: Session | None = None) -> bool:
        deleted = False
        if db is not None:
            query = db.query(HealthSnapshotModel).filter(HealthSnapshotModel.id == snapshot_id)
            if user_id is not None:
                query = query.filter(HealthSnapshotModel.user_id == user_id)
            s = query.first()
            if s:
                db.delete(s)
                db.commit()
                deleted = True

        if snapshot_id in self._snapshots:
            snap = self._snapshots[snapshot_id]
            snap_user = getattr(snap, "_user_id", None)
            if user_id is None or snap_user is None or snap_user == user_id:
                del self._snapshots[snapshot_id]
                deleted = True

        return deleted

    def clear_history(self, user_id: str | None = None, db: Session | None = None) -> int:
        count = 0
        if db is not None:
            query = db.query(HealthSnapshotModel)
            if user_id is not None:
                query = query.filter(HealthSnapshotModel.user_id == user_id)
            count = query.delete(synchronize_session=False)
            db.commit()

        count_mem = len(self._snapshots)
        self._snapshots.clear()
        return max(count, count_mem)

    def _determine_direction(self, change: float, tolerance: float | None = None) -> TrendDirection:
        tol = tolerance if tolerance is not None else self.stability_tolerance
        if abs(change) < tol:
            return "stable"
        return "increasing" if change > 0 else "decreasing"

    def _build_metric_trend(
        self,
        metric: str,
        display_name: str,
        curr_val: float | None,
        prev_val: float | None,
        tolerance: float | None = None,
    ) -> MetricTrendItem | None:
        if curr_val is None:
            return None

        if prev_val is None:
            return MetricTrendItem(
                metric=metric,
                display_name=display_name,
                current_value=round(curr_val, 4),
                previous_value=None,
                absolute_change=0.0,
                percentage_change=None,
                direction="stable",
            )

        change = round(curr_val - prev_val, 4)
        pct_change = round((change / prev_val) * 100.0, 2) if prev_val != 0 else None
        direction = self._determine_direction(change, tolerance)

        return MetricTrendItem(
            metric=metric,
            display_name=display_name,
            current_value=round(curr_val, 4),
            previous_value=round(prev_val, 4),
            absolute_change=change,
            percentage_change=pct_change,
            direction=direction,
        )

    def calculate_trends(
        self,
        custom_snapshots: list[HealthSnapshot] | None = None,
        user_id: str | None = None,
        db: Session | None = None,
    ) -> HealthTrendSummary:
        if custom_snapshots is not None:
            snaps = custom_snapshots
        elif db is not None and user_id is not None:
            snaps = self.get_history(user_id=user_id, db=db).snapshots
        else:
            snaps = list(self._snapshots.values())

        chronological_snaps = sorted(snaps, key=lambda s: s.timestamp)

        trend_points: list[HealthTrendPoint] = []
        for s in chronological_snaps:
            inp = s.assessment_input or {}
            dis = s.disease_results or {}
            rf = s.risk_fusion or {}

            ov_risk = float(rf.get("overall_risk_score", 0.0))
            ov_health = int(rf.get("overall_health_score", 100))

            heart_r = float(dis.get("heart", {}).get("risk_score")) if dis.get("heart") else None
            diab_r = float(dis.get("diabetes", {}).get("risk_score")) if dis.get("diabetes") else None
            htn_r = float(dis.get("hypertension", {}).get("risk_score")) if dis.get("hypertension") else None
            obes_r = float(dis.get("obesity", {}).get("risk_score")) if dis.get("obesity") else None

            bmi_val = float(inp["bmi"]) if inp.get("bmi") is not None else None
            sys_bp = float(inp["systolic_bp"]) if inp.get("systolic_bp") is not None else (float(inp["systolic_bp_mmHg"]) if inp.get("systolic_bp_mmHg") is not None else None)
            dia_bp = float(inp["diastolic_bp"]) if inp.get("diastolic_bp") is not None else (float(inp["diastolic_bp_mmHg"]) if inp.get("diastolic_bp_mmHg") is not None else None)
            gluc_val = float(inp["glucose"]) if inp.get("glucose") is not None else None
            hba1c_val = float(inp["hba1c"]) if inp.get("hba1c") is not None else None

            trend_points.append(
                HealthTrendPoint(
                    snapshot_id=s.id,
                    timestamp=s.timestamp,
                    overall_risk_score=ov_risk,
                    overall_health_score=ov_health,
                    heart_risk=heart_r,
                    diabetes_risk=diab_r,
                    hypertension_risk=htn_r,
                    obesity_risk=obes_r,
                    bmi=bmi_val,
                    systolic_bp=sys_bp,
                    diastolic_bp=dia_bp,
                    glucose=gluc_val,
                    hba1c=hba1c_val,
                )
            )

        if not trend_points:
            dummy_metric = MetricTrendItem(
                metric="overall_risk_score",
                display_name="Overall Risk Score",
                current_value=0.0,
                previous_value=None,
                absolute_change=0.0,
                percentage_change=None,
                direction="stable",
            )
            return HealthTrendSummary(
                trend_points=[],
                risk_trends=RiskTrendSummary(overall=dummy_metric),
                biomarker_trends=[],
                total_snapshots_evaluated=0,
            )

        curr_p = trend_points[-1]
        prev_p = trend_points[-2] if len(trend_points) >= 2 else None

        overall_trend = self._build_metric_trend(
            "overall_risk_score",
            "Overall Health Risk",
            curr_p.overall_risk_score,
            prev_p.overall_risk_score if prev_p else None,
        )
        heart_trend = self._build_metric_trend(
            "heart_risk",
            "Heart Disease Risk",
            curr_p.heart_risk,
            prev_p.heart_risk if prev_p else None,
        )
        diab_trend = self._build_metric_trend(
            "diabetes_risk",
            "Diabetes Risk",
            curr_p.diabetes_risk,
            prev_p.diabetes_risk if prev_p else None,
        )
        htn_trend = self._build_metric_trend(
            "hypertension_risk",
            "Hypertension Risk",
            curr_p.hypertension_risk,
            prev_p.hypertension_risk if prev_p else None,
        )
        obes_trend = self._build_metric_trend(
            "obesity_risk",
            "Obesity Risk",
            curr_p.obesity_risk,
            prev_p.obesity_risk if prev_p else None,
        )

        risk_trends = RiskTrendSummary(
            overall=overall_trend,
            heart=heart_trend,
            diabetes=diab_trend,
            hypertension=htn_trend,
            obesity=obes_trend,
        )

        biomarker_list: list[MetricTrendItem] = []
        for key, name, c_v, p_v, tol in [
            ("systolic_bp", "Systolic Blood Pressure", curr_p.systolic_bp, prev_p.systolic_bp if prev_p else None, 2.0),
            ("diastolic_bp", "Diastolic Blood Pressure", curr_p.diastolic_bp, prev_p.diastolic_bp if prev_p else None, 2.0),
            ("glucose", "Blood Glucose Level", curr_p.glucose, prev_p.glucose if prev_p else None, 5.0),
            ("hba1c", "HbA1c Level", curr_p.hba1c, prev_p.hba1c if prev_p else None, 0.2),
            ("bmi", "Body Mass Index", curr_p.bmi, prev_p.bmi if prev_p else None, 0.5),
        ]:
            b_item = self._build_metric_trend(key, name, c_v, p_v, tol)
            if b_item:
                biomarker_list.append(b_item)

        return HealthTrendSummary(
            trend_points=trend_points,
            risk_trends=risk_trends,
            biomarker_trends=biomarker_list,
            total_snapshots_evaluated=len(trend_points),
        )


history_service = HistoryService.get_instance()
