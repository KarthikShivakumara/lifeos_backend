from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class ProfilePayload(BaseModel):
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_group: str | None = None
    goals: str | None = None
    medical_history: str | None = None


class UserRead(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: str


class UserProfileRead(UserRead):
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_group: str | None = None
    goals: str | None = None
    medical_history: str | None = None

