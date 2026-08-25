from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LifestyleRecord(Base):
    __tablename__ = "lifestyle_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("health_assessments.id"), unique=True, nullable=False)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0)
    diet_score: Mapped[float] = mapped_column(Float, default=0.0)
    sleep_score: Mapped[float] = mapped_column(Float, default=0.0)
    stress_score: Mapped[float] = mapped_column(Float, default=0.0)
    habits_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    assessment = relationship("HealthAssessment", back_populates="lifestyle_record")

