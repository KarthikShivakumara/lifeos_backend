from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DiseaseResult(Base):
    __tablename__ = "disease_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("health_assessments.id"), nullable=False)
    disease: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    assessment = relationship("HealthAssessment", backref="disease_results")
    shap_results = relationship("SHAPResult", back_populates="disease_result", cascade="all, delete-orphan")
