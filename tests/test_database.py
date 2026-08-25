from __future__ import annotations

import json
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.disease_result import DiseaseResult
from app.models.health_assessment import HealthAssessment
from app.models.health_snapshot import HealthSnapshotModel
from app.models.recommendation_result import RecommendationResultModel
from app.models.risk_fusion_result import RiskFusionResultModel
from app.models.shap_result import SHAPResult
from app.models.user import User


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_database_models_creation_and_relationships() -> None:
    db = SessionLocal()
    try:
        # Create User
        user = User(full_name="Bob Test", email="bob@lifeos.ai", password_hash="hashed_secret")
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.id is not None

        # Create HealthAssessment
        assessment = HealthAssessment(
            user_id=user.id,
            systolic_bp=140,
            diastolic_bp=90,
            bmi=28.5,
            sleep_hours=7.0,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        assert assessment.user_id == user.id

        # Create DiseaseResult
        dis_res = DiseaseResult(
            assessment_id=assessment.id,
            disease="heart",
            risk_score=0.45,
            risk_level="moderate",
            prediction=1,
            threshold=0.40,
            model="XGBoost",
        )
        db.add(dis_res)
        db.commit()
        db.refresh(dis_res)

        # Create SHAPResult
        shap = SHAPResult(
            disease_result_id=dis_res.id,
            feature="systolic_bp_mmHg",
            contribution=1.245,
            direction="increases_risk",
        )
        db.add(shap)

        # Create RiskFusionResult
        rf = RiskFusionResultModel(
            assessment_id=assessment.id,
            overall_risk_score=0.45,
            overall_risk_percentage=45.0,
            overall_risk_level="moderate",
            overall_health_score=55,
            top_priority_disease="heart",
        )
        db.add(rf)

        # Create RecommendationResult
        rec = RecommendationResultModel(
            assessment_id=assessment.id,
            recommendations_json=json.dumps([{"title": "Monitor BP"}]),
        )
        db.add(rec)

        # Create HealthSnapshotModel
        snap = HealthSnapshotModel(
            id="snap-db-test",
            user_id=user.id,
            timestamp="2026-08-20T12:00:00Z",
            assessment_input_json=json.dumps({"systolic_bp": 140}),
            disease_results_json=json.dumps({"heart": {"risk_score": 0.45}}),
        )
        db.add(snap)

        db.commit()

        # Query and verify
        queried_user = db.query(User).filter(User.id == user.id).first()
        assert queried_user is not None
        assert len(queried_user.assessments) == 1

        queried_snap = db.query(HealthSnapshotModel).filter(HealthSnapshotModel.user_id == user.id).first()
        assert queried_snap is not None
        assert queried_snap.id == "snap-db-test"
    finally:
        db.close()
