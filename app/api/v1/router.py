from fastapi import APIRouter

from app.api.v1.endpoints import (
    adaptive,
    admin,
    assessments,
    assistant,
    auth,
    ckd,
    coach,
    diabetes,
    heart,
    history,
    hypertension,
    notifications,
    nutrition,
    obesity,
    pipeline,
    predictions,
    recommendations,
    reports,
    risk_fusion,
    sensors,
    sleep,
    stroke,
    twin,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(assessments.router)
api_router.include_router(pipeline.router)
api_router.include_router(twin.router)
api_router.include_router(predictions.router)
api_router.include_router(recommendations.router)
api_router.include_router(history.router)
api_router.include_router(notifications.router)
api_router.include_router(assistant.router)
api_router.include_router(coach.router)
api_router.include_router(reports.router)
api_router.include_router(sensors.router)
api_router.include_router(admin.router)
api_router.include_router(heart.router)
api_router.include_router(diabetes.router)
api_router.include_router(hypertension.router)
api_router.include_router(obesity.router)
api_router.include_router(stroke.router)
api_router.include_router(ckd.router)
api_router.include_router(sleep.router)
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(risk_fusion.router)
api_router.include_router(adaptive.router)
