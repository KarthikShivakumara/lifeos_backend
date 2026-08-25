from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RiskFusionResultModel(Base):
    __tablename__ = "risk_fusion_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("health_assessments.id"), nullable=False)
    overall_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_risk_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    overall_risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_health_score: Mapped[int] = mapped_column(Integer, nullable=False)
    top_priority_disease: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    assessment = relationship("HealthAssessment", backref="risk_fusion_result")
