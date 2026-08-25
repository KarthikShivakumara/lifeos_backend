from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class SensorDataCreate(BaseModel):
    device_id: str | None = None
    sensor_type: str
    value: float
    unit: str | None = None
    metadata_json: str | None = None
    recorded_at: datetime | None = None


class SensorDataRead(ORMModel):
    id: str
    user_id: str
    device_id: str | None
    sensor_type: str
    value: float
    unit: str | None
    metadata_json: str | None
    recorded_at: datetime

