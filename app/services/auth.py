from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.security.password import validate_password_strength
from app.models.user import User


def _ensure_bcrypt_compatible(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer.")


def register_user(db: Session, full_name: str, email: str, password: str, role: str = "user") -> User:
    _ensure_bcrypt_compatible(password)
    valid, msg = validate_password_strength(password)
    if not valid:
        raise ValueError(msg)

    clean_email = email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise ValueError("Email already registered")
    user = User(full_name=full_name.strip(), email=clean_email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    _ensure_bcrypt_compatible(password)
    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_user_token(user: User) -> str:
    return create_access_token(subject=user.id, extra={"role": user.role, "email": user.email})
