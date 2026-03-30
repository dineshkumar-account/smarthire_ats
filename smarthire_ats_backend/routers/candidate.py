from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import require_roles
from models.user import User, UserRole
from services import candidate_service

router = APIRouter(prefix="/candidate", tags=["candidate"])
candidate_user = require_roles(UserRole.candidate)


@router.get("/dashboard")
def candidate_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(candidate_user),
) -> dict:
    return candidate_service.get_candidate_dashboard(db, current_user.id)
