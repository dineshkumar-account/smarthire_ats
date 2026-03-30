from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.job import JobCreate, JobRead, JobUpdate
from services import job_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=201)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    try:
        job = job_service.create_job(db, current_user, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return JobRead.model_validate(job)


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int | None = Query(None),
    active_only: bool = Query(True),
) -> list[JobRead]:
    jobs = job_service.list_jobs(db, current_user, company_id=company_id, active_only=active_only)
    return [JobRead.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobRead)
def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    job = job_service.get_job(db, job_id, current_user)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    try:
        job = job_service.update_job(db, job_id, current_user, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return JobRead.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        job_service.delete_job(db, job_id, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
