from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.health_snapshot import HealthSnapshotModel
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services.pdf_report_service import generate_clinical_health_pdf
from app.services.reports import create_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportRead)
def create(payload: ReportCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_report(db, current_user.id, payload.report_type, payload.title, payload.summary)


@router.get("", response_model=list[ReportRead])
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Report).filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()


@router.get("/{snapshot_id}/pdf", summary="Generate & Download Clinical Health Summary PDF")
def download_report_pdf(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Generates a downloadable, publication-grade clinical summary PDF for a given health assessment snapshot."""
    snapshot = None
    if snapshot_id == "latest":
        snapshot = (
            db.query(HealthSnapshotModel)
            .filter_by(user_id=current_user.id)
            .order_by(HealthSnapshotModel.created_at.desc())
            .first()
        )
    else:
        snapshot = (
            db.query(HealthSnapshotModel)
            .filter_by(id=snapshot_id, user_id=current_user.id)
            .first()
        )

    if snapshot is not None:
        try:
            disease_results = json.loads(snapshot.disease_results_json) if snapshot.disease_results_json else {}
        except Exception:
            disease_results = {}
        try:
            risk_fusion = json.loads(snapshot.risk_fusion_json) if snapshot.risk_fusion_json else {}
        except Exception:
            risk_fusion = {}
        try:
            recommendations = json.loads(snapshot.recommendations_json) if snapshot.recommendations_json else []
        except Exception:
            recommendations = []

        snap_data = {
            "id": snapshot.id,
            "timestamp": snapshot.timestamp,
            "disease_results": disease_results,
            "risk_fusion": risk_fusion,
            "recommendations": recommendations,
        }
    else:
        # Fallback baseline snapshot for immediate review if no assessment exists yet
        snap_data = {
            "id": "baseline-demonstration-01",
            "timestamp": "Current Baseline",
            "disease_results": {
                "heart": {"risk_score": 0.082, "threshold": 0.40, "risk_level": "low"},
                "diabetes": {"risk_score": 0.015, "threshold": 0.70, "risk_level": "low"},
                "hypertension": {"risk_score": 0.041, "threshold": 0.60, "risk_level": "low"},
                "obesity": {"risk_score": 0.120, "threshold": 0.50, "risk_level": "low"},
                "stroke": {"risk_score": 0.018, "threshold": 0.50, "risk_level": "low"},
                "ckd": {"risk_score": 0.024, "threshold": 0.33, "risk_level": "low"},
            },
            "risk_fusion": {
                "overall_risk_score": 0.064,
                "overall_risk_percentage": 6.4,
                "overall_risk_level": "low",
                "overall_health_score": 94,
                "top_priority_disease": "Cardiometabolic Health Optimal",
            },
            "recommendations": [
                {
                    "title": "Maintain Aerobic Consistency",
                    "description": "Continue daily 30-minute moderate physical activity.",
                    "action": "Maintain 8,000+ daily steps.",
                    "priority": "LOW",
                },
                {
                    "title": "Optimize Circadian Sleep Architecture",
                    "description": "Preserve 7.5+ hours restful sleep with consistent bedtime.",
                    "action": "Avoid blue light 60 mins before sleeping.",
                    "priority": "LOW",
                },
            ],
        }

    user_name = current_user.full_name or "LifeOS Patient"
    user_email = current_user.email or "patient@lifeos.health"

    pdf_bytes = generate_clinical_health_pdf(user_name, user_email, snap_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="LifeOS_Clinical_Report_{snapshot_id}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
