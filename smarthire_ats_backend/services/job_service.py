from sqlalchemy import select
from sqlalchemy.orm import Session

from models.application import Application
from models.company import Company
from models.job import Job
from models.user import User, UserRole
from schemas.job import JobCreate, JobUpdate


def _delete_application_cascade(db: Session, application_id: int) -> None:
    from models.application_round import ApplicationRound
    from models.ats_analysis import AtsAnalysis

    app = db.get(Application, application_id)
    if app is None:
        return
    for row in list(db.scalars(select(ApplicationRound).where(ApplicationRound.application_id == application_id)).all()):
        db.delete(row)
    for row in list(db.scalars(select(AtsAnalysis).where(AtsAnalysis.application_id == application_id)).all()):
        db.delete(row)
    db.delete(app)


def delete_job_cascade(db: Session, job_id: int) -> None:
    apps = db.scalars(select(Application).where(Application.job_id == job_id)).all()
    for a in apps:
        _delete_application_cascade(db, a.id)
    job = db.get(Job, job_id)
    if job:
        db.delete(job)


def _can_manage_company(db: Session, company_id: int, user: User) -> bool:
    if user.role == UserRole.admin:
        return True
    company = db.get(Company, company_id)
    return company is not None and company.owner_id == user.id


def create_job(db: Session, user: User, payload: JobCreate) -> Job:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise ValueError("Company not found")
    if not _can_manage_company(db, payload.company_id, user):
        raise PermissionError("Cannot create jobs for this company")
    job = Job(
        title=payload.title.strip(),
        description=payload.description,
        skills_required=payload.skills_required,
        experience_min=payload.experience_min,
        company_id=payload.company_id,
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(
    db: Session,
    user: User,
    company_id: int | None = None,
    active_only: bool = True,
) -> list[Job]:
    if user.role == UserRole.candidate:
        stmt = select(Job).where(Job.is_active.is_(True)).order_by(Job.id.desc())
        if company_id is not None:
            stmt = stmt.where(Job.company_id == company_id)
        return list(db.scalars(stmt).all())
    stmt = select(Job).join(Company, Job.company_id == Company.id).order_by(Job.id.desc())
    if user.role != UserRole.admin:
        stmt = stmt.where(Company.owner_id == user.id)
    if company_id is not None:
        stmt = stmt.where(Job.company_id == company_id)
    if active_only:
        stmt = stmt.where(Job.is_active.is_(True))
    return list(db.scalars(stmt).all())


def get_job(db: Session, job_id: int, user: User) -> Job | None:
    job = db.get(Job, job_id)
    if job is None:
        return None
    if user.role == UserRole.candidate:
        return job if job.is_active else None
    if user.role == UserRole.admin:
        return job
    company = db.get(Company, job.company_id)
    if company and company.owner_id == user.id:
        return job
    return None


def update_job(db: Session, job_id: int, user: User, payload: JobUpdate) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise ValueError("Job not found")
    if not _can_manage_company(db, job.company_id, user):
        raise PermissionError("Cannot update this job")
    if payload.title is not None:
        job.title = payload.title.strip()
    if payload.description is not None:
        job.description = payload.description
    if payload.skills_required is not None:
        job.skills_required = payload.skills_required
    if payload.experience_min is not None:
        job.experience_min = payload.experience_min
    if payload.is_active is not None:
        job.is_active = payload.is_active
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job_id: int, user: User) -> None:
    job = db.get(Job, job_id)
    if job is None:
        raise ValueError("Job not found")
    if not _can_manage_company(db, job.company_id, user):
        raise PermissionError("Cannot delete this job")
    delete_job_cascade(db, job_id)
    db.commit()
