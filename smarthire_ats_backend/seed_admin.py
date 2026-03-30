"""Create default admin if missing. Run from this folder: python seed_admin.py"""
from sqlalchemy import select

from db.base import Base
from db.session import SessionLocal, engine
import models  # noqa: F401 — register mappers
from models.user import User, UserRole
from utils.hash import get_password_hash


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Default admin for first-time access.
        # NOTE: Public /auth/register is candidate-only; admin must be created here
        # (or via existing admin-only endpoints).
        # Default first-time admin credential.
        # Note: backend response schema accepts "admin" as-is for email.
        desired_email = "admin"
        password = "admin"

        existing_admin = db.scalars(select(User).where(User.role == UserRole.admin)).first()
        if existing_admin:
            # If an admin was seeded previously with a non-email value (e.g. "admin"),
            # fix the email to keep /auth/login validation (EmailStr) working.
            if existing_admin.email != desired_email:
                conflict = db.scalars(select(User).where(User.email == desired_email)).first()
                if conflict:
                    print(f"Admin exists, but desired email {desired_email} is already taken. No changes made.")
                    return
                existing_admin.email = desired_email
                db.add(existing_admin)
                db.commit()
            print("Admin user already exists. Seed ensured.")
            return

        if db.scalars(select(User).where(User.email == desired_email)).first():
            print(f"User {desired_email} already exists but is not admin. No changes made.")
            return
        user = User(
            email=desired_email,
            password_hash=get_password_hash(password),
            name="Admin",
            role=UserRole.admin,
        )
        db.add(user)
        db.commit()
        print(f"Created default admin: {desired_email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
