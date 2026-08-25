import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password against security policy rules.
    - Min 8 chars
    - Must contain uppercase
    - Must contain lowercase
    - Must contain digit
    - Must contain special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character."
    return True, "Password meets security standards."


def hash_password(password: str) -> str:
    """Hash plaintext password securely using pbkdf2_sha256/bcrypt."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored hash."""
    return pwd_context.verify(password, hashed_password)
