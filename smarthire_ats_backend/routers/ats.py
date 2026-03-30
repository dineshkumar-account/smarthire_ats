from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.ats_analysis import AtsAnalysisRead
from services import ats_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/analyze/{application_id}", response_model=AtsAnalysisRead)
def analyze_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AtsAnalysisRead:
    try:
        row = ats_service.analyze_application(db, application_id, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return AtsAnalysisRead.model_validate(row)
