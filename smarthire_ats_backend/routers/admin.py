from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import require_roles
from models.user import User, UserRole
from schemas.company import CompanyRead
from schemas.user import UserRead
from services import admin_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/admin", tags=["admin"])
admin_user = require_roles(UserRole.admin)


class RecruiterCreatePayload(BaseModel):
    email: EmailStr
    password: str
    name: str


class ResetPasswordPayload(BaseModel):
    password: str


@router.post("/recruiters", response_model=UserRead, status_code=201)
def create_recruiter(
    payload: RecruiterCreatePayload,
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> UserRead:
    try:
        user = admin_service.create_recruiter(db, payload.model_dump())
    except ValueError as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)


@router.post("/admins", response_model=UserRead, status_code=201)
def create_admin(
    payload: RecruiterCreatePayload,
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> UserRead:
    try:
        user = admin_service.create_admin(db, payload.model_dump())
    except ValueError as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)


@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_dashboard(db)


@router.get("/companies", response_model=list[CompanyRead])
def admin_companies(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> list[CompanyRead]:
    companies = admin_service.list_companies_admin(db)
    return [CompanyRead.model_validate(c) for c in companies]


@router.get("/applicants")
def admin_applicants(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_applicants(db, current_user.id)


@router.get("/users", response_model=list[UserRead])
def admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
    roles: list[str] | None = Query(default=None),
) -> list[UserRead]:
    role_enums: list[UserRole] | None = None
    if roles:
        role_enums = []
        for r in roles:
            try:
                role_enums.append(UserRole(r))
            except ValueError:
                continue
    users = admin_service.list_users_by_roles(db, role_enums)
    return [UserRead.model_validate(u) for u in users]


@router.put("/reset-password/admin/{user_id}", response_model=UserRead)
def reset_admin_password(
    user_id: int,
    payload: ResetPasswordPayload,
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> UserRead:
    try:
        user = admin_service.reset_user_password(db, user_id, UserRole.admin, payload.password)
    except ValueError as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)


@router.put("/reset-password/recruiter/{user_id}", response_model=UserRead)
def reset_recruiter_password(
    user_id: int,
    payload: ResetPasswordPayload,
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> UserRead:
    try:
        user = admin_service.reset_user_password(db, user_id, UserRole.recruiter, payload.password)
    except ValueError as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)


@router.put("/reset-password/candidate/{user_id}", response_model=UserRead)
def reset_candidate_password(
    user_id: int,
    payload: ResetPasswordPayload,
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> UserRead:
    try:
        user = admin_service.reset_user_password(db, user_id, UserRole.candidate, payload.password)
    except ValueError as e:
        raise_service_exception(e)
    return UserRead.model_validate(user)


@router.get("/recruiter-dashboard")
def admin_recruiter_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_recruiter_dashboard(db)


@router.get("/recruiter-dashboard/stats")
def admin_recruiter_dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_recruiter_dashboard_stats(db)


@router.get("/recruiter-dashboard/job-performance")
def admin_recruiter_dashboard_job_performance(
    days: int = Query(30),
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_recruiter_job_performance(db, days=days)


@router.get("/recruiter-dashboard/applicant-stages")
def admin_recruiter_dashboard_applicant_stages(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_recruiter_applicant_stages(db)


@router.get("/recruiter-dashboard/google-forms/recent")
def admin_recruiter_dashboard_google_forms_recent(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    return admin_service.get_admin_recruiter_google_forms_recent(db)


@router.get("/candidate-dashboard/registered")
def admin_candidate_dashboard_registered(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> list[dict]:
    return admin_service.get_admin_candidate_dashboard_registered(db)


@router.get("/candidate-dashboard/google-form")
def admin_candidate_dashboard_google_form(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> list[dict]:
    return admin_service.get_admin_candidate_dashboard_google_form(db)


@router.get("/candidate-dashboard")
def admin_candidate_dashboard_all(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
) -> dict:
    registered = admin_service.get_admin_candidate_dashboard_registered(db)
    google_form = admin_service.get_admin_candidate_dashboard_google_form(db)
    return {"registered": registered, "google_form": google_form}
