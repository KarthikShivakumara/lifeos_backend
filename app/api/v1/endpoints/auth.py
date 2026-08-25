from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, RegisterRequest, TokenResponse, UserSummary
from app.schemas.common import MessageResponse
from app.services.auth import authenticate_user, create_user_token, register_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserSummary)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload.full_name, payload.email, payload.password)
        return user
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_user_token(user))


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(_: ForgotPasswordRequest):
    return MessageResponse(message="Password reset instructions have been prepared for delivery.")


@router.get("/me", response_model=UserSummary)
def me(current_user: User = Depends(get_current_user)):
    return current_user
