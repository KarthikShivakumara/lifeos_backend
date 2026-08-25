from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sensor_type: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="sensor_data")

