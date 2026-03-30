from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.user import UserMe
from services import users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
def read_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserMe:
    u = users_service.get_me(db, current_user.id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserMe.model_validate(u)
