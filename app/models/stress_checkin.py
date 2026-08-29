from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StressCheckin(Base):
    __tablename__ = "stress_checkins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    # User self-reported assessment inputs (0-10 scale)
    perceived_stress: Mapped[int] = mapped_column(Integer, nullable=False)
    overwhelm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_relaxing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Lifestyle snapshot values captured alongside check-in
    sleep_hours_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_minutes_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Derived non-diagnostic wellness indicators
    stress_index: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0
    stress_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low, mild, moderate, high
    data_completeness: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0

    # Metadata & contextual notes
    source: Mapped[str] = mapped_column(String(50), default="user_checkin", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="stress_checkins")
