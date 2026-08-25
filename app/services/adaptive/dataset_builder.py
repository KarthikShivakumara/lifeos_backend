from __future__ import annotations

import logging, json
from pathlib import Path
from datetime import datetime
from typing import Any
import pandas as pd
from sqlalchemy.orm import Session

from app.models.adaptive import HealthEvent, OutcomeRecord, PredictionSnapshot

logger = logging.getLogger("lifeos.adaptive.dataset_builder")


def _get_adaptive_dataset_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    d_dir = root / "datasets_adaptive"
    d_dir.mkdir(exist_ok=True)
    for sub in ["raw", "validated", "candidates", "training", "validation", "rejected"]:
        (d_dir / sub).mkdir(exist_ok=True)
    return d_dir


def validate_record_quality(record: dict[str, Any]) -> tuple[bool, str]:
    """Applies strict data quality and clinical safety validation rules."""
    # Consent check
    if record.get("consent_status") != "granted":
        return False, "User consent not granted for model improvement"

    # Verification check
    if record.get("verification_status") != "VERIFIED":
        return False, "Outcome label is UNVERIFIED"

    # Biological age check
    age = record.get("age_years", record.get("age"))
    if age is not None and (age < 18 or age > 100):
        return False, f"Invalid age value {age}"

    # BMI check
    bmi = record.get("bmi")
    if bmi is not None and (bmi < 10 or bmi > 80):
        return False, f"Invalid BMI value {bmi}"

    # BP check
    sys_bp = record.get("systolic_bp_mmHg", record.get("systolic_bp"))
    if sys_bp is not None and (sys_bp < 70 or sys_bp > 250):
        return False, f"Invalid systolic BP value {sys_bp}"

    return True, "VALID"


def build_candidate_dataset(db: Session, disease_name: str) -> dict[str, Any]:
    """Extracts, validates, de-identifies, and writes candidate dataset for model training."""
    d_dir = _get_adaptive_dataset_dir()
    dis_dir = d_dir / "candidates" / disease_name
    dis_dir.mkdir(parents=True, exist_ok=True)
    rej_dir = d_dir / "rejected" / disease_name
    rej_dir.mkdir(parents=True, exist_ok=True)

    outcomes = (
        db.query(OutcomeRecord)
        .filter(OutcomeRecord.outcome_type.like(f"%{disease_name}%"))
        .all()
    )

    valid_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []

    for out in outcomes:
        snap = None
        if out.related_prediction_id:
            snap = db.query(PredictionSnapshot).filter(PredictionSnapshot.id == out.related_prediction_id).first()

        rec = {
            "subject_id": f"sub-{out.user_id[:8]}",  # De-identified subject ID
            "outcome_label": out.outcome_label or out.outcome_value,
            "verification_status": out.verification_status,
            "consent_status": out.consent_status,
            "timestamp": out.measurement_date.isoformat(),
        }

        if snap and snap.feature_snapshot:
            rec.update(snap.feature_snapshot)

        is_valid, reason = validate_record_quality(rec)
        if is_valid:
            valid_records.append(rec)
        else:
            rec["rejection_reason"] = reason
            rejected_records.append(rec)

    # Write files if records exist
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    cand_path = dis_dir / f"{disease_name}_candidate_{timestamp_str}.json"
    rej_path = rej_dir / f"{disease_name}_rejected_{timestamp_str}.json"

    with open(cand_path, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2)

    with open(rej_path, "w", encoding="utf-8") as f:
        json.dump(rejected_records, f, indent=2)

    logger.info(f"Dataset Build Completed for {disease_name}: {len(valid_records)} valid, {len(rejected_records)} rejected.")
    return {
        "disease": disease_name,
        "valid_count": len(valid_records),
        "rejected_count": len(rejected_records),
        "candidate_file": str(cand_path),
        "rejected_file": str(rej_path),
    }
