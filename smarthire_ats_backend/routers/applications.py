from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.application import ApplicationRead, ApplicationUpdate
from services import application_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(
    job_id: int = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    file_bytes = await resume.read()
    try:
        app = application_service.create_application_from_pdf(db, current_user.id, job_id, file_bytes)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return ApplicationRead.model_validate(app)


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_id: int | None = Query(None),
) -> list[ApplicationRead]:
    apps = application_service.list_applications(db, current_user, job_id=job_id)
    return [ApplicationRead.model_validate(a) for a in apps]


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    app = application_service.get_application(db, application_id, current_user)
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationRead.model_validate(app)


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationRead:
    try:
        app = application_service.update_application(db, application_id, current_user, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return ApplicationRead.model_validate(app)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        application_service.delete_application(db, application_id, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
