from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.user import ProfilePayload, UserProfileRead

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserProfileRead)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "age": profile.age if profile else None,
        "gender": profile.gender if profile else None,
        "height_cm": profile.height_cm if profile else None,
        "weight_kg": profile.weight_kg if profile else None,
        "blood_group": profile.blood_group if profile else None,
        "goals": profile.goals if profile else None,
        "medical_history": profile.medical_history if profile else None,
    }
    return data


@router.put("/me/profile", response_model=UserProfileRead)
def update_profile(payload: ProfilePayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    profile.age = payload.age
    profile.gender = payload.gender
    profile.height_cm = payload.height_cm
    profile.weight_kg = payload.weight_kg
    profile.blood_group = payload.blood_group
    profile.goals = payload.goals
    profile.medical_history = payload.medical_history
    db.commit()
    db.refresh(profile)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "blood_group": profile.blood_group,
        "goals": profile.goals,
        "medical_history": profile.medical_history,
    }
