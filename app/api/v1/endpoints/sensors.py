from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.sensor_data import SensorData
from app.models.user import User
from app.schemas.sensor import SensorDataCreate, SensorDataRead
from app.services.sensors import ingest_sensor_reading

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post("", response_model=SensorDataRead)
def ingest(payload: SensorDataCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ingest_sensor_reading(db, current_user.id, payload)


@router.get("", response_model=list[SensorDataRead])
def list_sensor_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SensorData).filter_by(user_id=current_user.id).order_by(SensorData.recorded_at.desc()).all()

