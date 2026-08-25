from sqlalchemy.orm import Session

from app.models.sensor_data import SensorData
from app.schemas.sensor import SensorDataCreate


def ingest_sensor_reading(db: Session, user_id: str, payload: SensorDataCreate) -> SensorData:
    sensor = SensorData(
        user_id=user_id,
        device_id=payload.device_id,
        sensor_type=payload.sensor_type,
        value=payload.value,
        unit=payload.unit,
        metadata_json=payload.metadata_json,
        recorded_at=payload.recorded_at,
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor

