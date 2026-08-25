from __future__ import annotations

import logging
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session

from app.models.adaptive import DriftReport, PredictionSnapshot

logger = logging.getLogger("lifeos.adaptive.drift_service")


def monitor_feature_drift(db: Session, model_name: str, model_version: str = "1.0.0") -> list[DriftReport]:
    """Monitors feature distribution drift between early historical predictions and current population."""
    snapshots = (
        db.query(PredictionSnapshot)
        .filter(PredictionSnapshot.model_name == model_name)
        .order_by(PredictionSnapshot.timestamp.asc())
        .all()
    )

    if len(snapshots) < 10:
        logger.info(f"Insufficient prediction snapshots for drift analysis on {model_name}.")
        return []

    split_idx = max(5, int(len(snapshots) * 0.3))
    baseline_snaps = snapshots[:split_idx]
    current_snaps = snapshots[split_idx:]

    drift_reports: list[DriftReport] = []

    # Check key numerical features
    features_to_check = ["age_years", "bmi", "systolic_bp_mmHg", "blood_glucose_level"]

    for feat in features_to_check:
        base_vals = [s.feature_snapshot[feat] for s in baseline_snaps if s.feature_snapshot and feat in s.feature_snapshot and s.feature_snapshot[feat] is not None]
        curr_vals = [s.feature_snapshot[feat] for s in current_snaps if s.feature_snapshot and feat in s.feature_snapshot and s.feature_snapshot[feat] is not None]

        if not base_vals or not curr_vals:
            continue

        b_mean = float(np.mean(base_vals))
        c_mean = float(np.mean(curr_vals))
        b_std = float(np.std(base_vals)) if len(base_vals) > 1 else 1.0

        # Normalized mean shift
        drift_score = abs(c_mean - b_mean) / (b_std + 1e-5)
        severity = "LOW"
        if drift_score > 1.5:
            severity = "HIGH"
        elif drift_score > 0.7:
            severity = "MODERATE"

        report = DriftReport(
            model_name=model_name,
            model_version=model_version,
            feature=feat,
            baseline_mean=b_mean,
            current_mean=c_mean,
            drift_score=float(drift_score),
            severity=severity,
            timestamp=datetime.utcnow(),
        )
        db.add(report)
        drift_reports.append(report)

    db.commit()
    logger.info(f"Drift monitoring completed for {model_name}: {len(drift_reports)} reports generated.")
    return drift_reports


def get_drift_reports(db: Session, model_name: str | None = None) -> list[DriftReport]:
    query = db.query(DriftReport)
    if model_name:
        query = query.filter(DriftReport.model_name == model_name)
    return query.order_by(DriftReport.timestamp.desc()).all()
