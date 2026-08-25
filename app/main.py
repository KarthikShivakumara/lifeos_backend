import logging, time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.assistant import router as assistant_router
from app.api.v1.endpoints.diabetes import router as diabetes_router
from app.api.v1.endpoints.heart import router as heart_router
from app.api.v1.endpoints.history import router as history_router
from app.api.v1.endpoints.hypertension import router as hypertension_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.obesity import router as obesity_router
from app.api.v1.endpoints.recommendations import router as recommendations_router
from app.api.v1.endpoints.risk_fusion import router as risk_fusion_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base  # noqa: F401
from app.db.session import engine
from app.services.diabetes_model_service import diabetes_service
from app.services.heart_model_service import heart_service
from app.services.hypertension_model_service import hypertension_service
from app.services.obesity_model_service import obesity_service

logger = logging.getLogger("lifeos.main")
settings = get_settings()

# Simple in-memory rate limiting tracker (IP -> timestamps list)
RATE_LIMIT_STORE: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 60  # max 60 requests per minute per IP
RATE_LIMIT_WINDOW_SECONDS = 60


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup logic
    logger.info("Initializing LifeOS database tables...")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as err:
        logger.warning("Database initialization warning: %s", err)

    logger.info("Pre-loading Heart Disease model artifact...")
    try:
        heart_service.load_model()
    except Exception as err:
        logger.error("Failed to pre-load Heart Disease model: %s", err)

    logger.info("Pre-loading Diabetes model artifact...")
    try:
        diabetes_service.load_model()
    except Exception as err:
        logger.error("Failed to pre-load Diabetes model: %s", err)

    logger.info("Pre-loading Hypertension model artifact...")
    try:
        hypertension_service.load_model()
    except Exception as err:
        logger.error("Failed to pre-load Hypertension model: %s", err)

    logger.info("Pre-loading Obesity model artifact...")
    try:
        obesity_service.load_model()
    except Exception as err:
        logger.error("Failed to pre-load Obesity model: %s", err)

    yield

    # Shutdown logic
    logger.info("Shutting down LifeOS application...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LifeOS Health Risk Prediction & Analytics Backend",
    lifespan=lifespan,
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Security Headers & Rate Limiting Middleware
@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # Rate limit check for auth & assistant endpoints (supports reverse proxy X-Forwarded-For header)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.headers.get("x-real-ip"):
        client_ip = request.headers.get("x-real-ip", "").strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"

    now = time.time()

    # Clean old requests outside window
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]

    if client_ip != "testclient" and len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please wait before sending more requests."},
        )

    RATE_LIMIT_STORE[client_ip].append(now)

    response: Response = await call_next(request)

    # Attach Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include v1 API router (/api/v1/...)
app.include_router(api_router)

# Include /api direct endpoints
app.include_router(heart_router, prefix="/api")
app.include_router(diabetes_router, prefix="/api")
app.include_router(hypertension_router, prefix="/api")
app.include_router(obesity_router, prefix="/api")
app.include_router(risk_fusion_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")


@app.get("/health", tags=["Health Check"])
def health() -> dict[str, str]:
    heart_status = heart_service.get_health_status()
    diabetes_status = diabetes_service.get_health_status()
    hypertension_status = hypertension_service.get_health_status()
    obesity_status = obesity_service.get_health_status()
    all_ok = (
        heart_status.status == "ok"
        and diabetes_status.status == "ok"
        and hypertension_status.status == "ok"
        and obesity_status.status == "ok"
    )
    return {
        "status": "ok" if all_ok else "degraded",
        "service": "lifeos-api",
        "heart_model": heart_status.heart_model,
        "diabetes_model": diabetes_status.diabetes_model,
        "hypertension_model": hypertension_status.hypertension_model,
        "obesity_model": obesity_status.obesity_model,
        "heart_model_name": heart_status.model,
        "diabetes_model_name": diabetes_status.model,
        "hypertension_model_name": hypertension_status.model,
        "obesity_model_name": obesity_status.model,
    }
