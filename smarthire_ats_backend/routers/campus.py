from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from services import campus_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/campus", tags=["campus"])


@router.post("/import")
async def import_campus_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    data = await file.read()
    try:
        return campus_service.import_candidates_from_csv(db, data)
    except ValueError as e:
        raise_service_exception(e)
