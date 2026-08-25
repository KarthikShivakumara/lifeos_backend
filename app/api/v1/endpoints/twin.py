from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.twin import build_health_twin

router = APIRouter(prefix="/health-twin", tags=["Health Twin"])


@router.get("")
def get_twin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_health_twin(db, current_user.id)

