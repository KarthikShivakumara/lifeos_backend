from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class HealthSnapshotModel(Base):
    __tablename__ = "health_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    timestamp: Mapped[str] = mapped_column(String(100), nullable=False)
    assessment_input_json: Mapped[str] = mapped_column(Text, nullable=False)
    disease_results_json: Mapped[str] = mapped_column(Text, nullable=False)
    risk_fusion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="health_snapshots")
