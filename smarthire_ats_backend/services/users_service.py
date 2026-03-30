from sqlalchemy.orm import Session

from models.user import User


def get_me(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
