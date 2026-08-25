from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SHAPResult(Base):
    __tablename__ = "shap_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    disease_result_id: Mapped[str] = mapped_column(String(36), ForeignKey("disease_results.id"), nullable=False)
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    disease_result = relationship("DiseaseResult", back_populates="shap_results")
