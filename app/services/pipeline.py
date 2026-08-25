from sqlalchemy.orm import Session

from app.ml.risk_models import engineer_risk_input, run_four_model_fusion
from app.ml.shap_adapter import compute_feature_importance
from app.models.health_assessment import HealthAssessment
from app.models.recommendation import Recommendation
from app.schemas.assessment import HealthAssessmentCreate
from app.schemas.pipeline import ModelSignalRead, PipelineResponse
from app.services.assessment import create_assessment, upsert_profile
from app.services.activity import log_activity
from app.services.prediction import create_prediction, predict_from_assessment
from app.services.recommendation import generate_recommendations
from app.services.twin import build_health_twin


def run_assessment_pipeline(db: Session, user_id: str, payload: HealthAssessmentCreate) -> PipelineResponse:
    upsert_profile(db, user_id, payload)
    assessment = create_assessment(db, user_id, payload)
    log_activity(db, user_id, "assessment_created", "health_assessment", assessment.id)

    prediction_result = predict_from_assessment(assessment)
    prediction = create_prediction(db, user_id, assessment, result=prediction_result)
    log_activity(db, user_id, "prediction_generated", "prediction", prediction.id)

    recommendations = generate_recommendations(db, user_id, prediction)
    if recommendations:
        log_activity(db, user_id, "recommendations_generated", "recommendation", recommendations[0].id, f"{len(recommendations)} recommendations created")

    twin = build_health_twin(db, user_id)

    return PipelineResponse(
        assessment=assessment,
        feature_engineering=prediction_result.feature_engineering,
        model_signals=[
            ModelSignalRead(model_name=signal.name, risk_score=signal.risk, rationale=signal.rationale)
            for signal in prediction_result.model_signals
        ],
        fused_risk=prediction_result.fused_risk,
        feature_importance=prediction_result.feature_importance,
        prediction=prediction,
        recommendations=recommendations,
        health_twin=twin,
    )
