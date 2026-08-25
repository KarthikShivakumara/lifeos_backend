from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assessment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("health_assessments.id"), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), default="heuristic-risk-engine")
    heart_disease_risk: Mapped[float] = mapped_column(Float, default=0.0)
    diabetes_risk: Mapped[float] = mapped_column(Float, default=0.0)
    hypertension_risk: Mapped[float] = mapped_column(Float, default=0.0)
    overall_health_risk: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    assessment = relationship("HealthAssessment", back_populates="prediction")

