from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User, UserRole
from schemas.auth import LoginRequest, RegisterRequest
from utils.hash import get_password_hash, verify_password


def register_user(db: Session, payload: RegisterRequest) -> User:
    email = payload.email.lower().strip()
    existing = db.scalars(select(User).where(User.email == email)).first()
    if existing:
        raise ValueError("Email already registered")
    # Enforce: common registration creates only candidates.
    # Recruiter/admin creation is handled by admin-only endpoints.
    role = UserRole.candidate
    user = User(
        email=email,
        password_hash=get_password_hash(payload.password),
        name=payload.name.strip(),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> User | None:
    email = payload.email.lower().strip()
    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        return None
    if not verify_password(payload.password, user.password_hash):
        return None
    return user
