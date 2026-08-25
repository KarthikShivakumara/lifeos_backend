from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class HealthAssessment(Base):
    __tablename__ = "health_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spo2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smoking_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alcohol_use: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercise_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    diet_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stress_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="assessments")
    lifestyle_record = relationship("LifestyleRecord", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    prediction = relationship("PredictionHistory", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

