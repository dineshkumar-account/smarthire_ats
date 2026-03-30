from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import require_roles
from models.user import User, UserRole
from schemas.application_round import ApplicationRoundRead, ApplicationRoundUpsertRequest
from schemas.google_form_link import (
    GoogleFormLinkCreateRequest,
    GoogleFormLinkRead,
    GoogleFormLinkUpdateRequest,
)
from services import application_round_service, google_form_link_service, recruiter_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/recruiter", tags=["recruiter"])
recruiter_user = require_roles(UserRole.recruiter, UserRole.admin)


@router.get("/dashboard")
def recruiter_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_recruiter_dashboard(db, current_user.id)


@router.get("/dashboard/stats")
def recruiter_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_dashboard_stats(db, current_user.id)


@router.get("/dashboard/job-performance")
def recruiter_dashboard_job_performance(
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_job_performance(db, current_user.id, days=days)


@router.get("/dashboard/applicant-stages")
def recruiter_dashboard_applicant_stages(
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_applicant_stages(db, current_user.id)


@router.get("/dashboard/google-forms/recent")
def recruiter_dashboard_google_forms_recent(
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_google_forms_recent(db, current_user.id)


@router.get("/applicants")
def recruiter_applicants(
    job_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> dict:
    return recruiter_service.get_recruiter_applicants(
        db,
        current_user.id,
        job_id=job_id,
        actor_role=current_user.role.value,
    )


@router.get(
    "/applications/{application_id}/rounds",
    response_model=list[ApplicationRoundRead],
)
def list_application_rounds(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> list[ApplicationRoundRead]:
    try:
        return application_round_service.list_rounds_for_application(db, application_id, current_user)
    except PermissionError as e:
        raise_service_exception(e)


@router.post(
    "/applications/{application_id}/rounds",
    response_model=ApplicationRoundRead,
)
def upsert_application_round(
    application_id: int,
    payload: ApplicationRoundUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> ApplicationRoundRead:
    try:
        return application_round_service.upsert_round(db, application_id, current_user, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)


@router.delete("/rounds/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application_round(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> None:
    try:
        application_round_service.delete_round(db, round_id, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)


@router.get("/google-forms", response_model=list[GoogleFormLinkRead])
def list_google_form_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> list[GoogleFormLinkRead]:
    try:
        return google_form_link_service.list_google_form_links(db, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return []


@router.post("/google-forms", response_model=GoogleFormLinkRead, status_code=status.HTTP_201_CREATED)
def create_google_form_link(
    payload: GoogleFormLinkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> GoogleFormLinkRead:
    try:
        return google_form_link_service.create_google_form_link(db, current_user, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stub")


@router.patch("/google-forms/{link_id}", response_model=GoogleFormLinkRead)
def update_google_form_link(
    link_id: int,
    payload: GoogleFormLinkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> GoogleFormLinkRead:
    try:
        return google_form_link_service.update_google_form_link(db, current_user, link_id, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stub")


@router.delete("/google-forms/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_google_form_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(recruiter_user),
) -> None:
    try:
        google_form_link_service.delete_google_form_link(db, current_user, link_id)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
