import io

import pdfplumber
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatus
from models.company import Company
from models.job import Job
from models.user import User, UserRole
from schemas.application import ApplicationUpdate
from services.job_service import _delete_application_cascade


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    parts: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
    except Exception:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="replace")
    return "\n".join(parts)


def create_application_from_pdf(db: Session, user_id: int, job_id: int, file_bytes: bytes) -> Application:
    job = db.get(Job, job_id)
    if job is None or not job.is_active:
        raise ValueError("Job not found or inactive")
    existing = db.scalars(
        select(Application).where(Application.user_id == user_id, Application.job_id == job_id)
    ).first()
    if existing:
        raise ValueError("Already applied to this job")
    resume_text = _extract_text_from_pdf(file_bytes)
    app = Application(
        user_id=user_id,
        job_id=job_id,
        resume_text=resume_text or None,
        status=ApplicationStatus.applied,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def _application_visible(db: Session, app: Application, user: User) -> bool:
    if app.user_id == user.id:
        return True
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.recruiter:
        job = db.get(Job, app.job_id)
        if job is None:
            return False
        company = db.get(Company, job.company_id)
        return company is not None and company.owner_id == user.id
    return False


def list_applications(db: Session, user: User, job_id: int | None = None) -> list[Application]:
    if user.role == UserRole.candidate:
        stmt = select(Application).where(Application.user_id == user.id).order_by(Application.submitted_at.desc())
        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        return list(db.scalars(stmt).all())
    stmt = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .order_by(Application.submitted_at.desc())
    )
    if user.role == UserRole.recruiter:
        stmt = stmt.where(Company.owner_id == user.id)
    if job_id is not None:
        stmt = stmt.where(Application.job_id == job_id)
    return list(db.scalars(stmt).all())


def get_application(db: Session, application_id: int, user: User) -> Application | None:
    app = db.get(Application, application_id)
    if app is None:
        return None
    return app if _application_visible(db, app, user) else None


def update_application(db: Session, application_id: int, user: User, payload: ApplicationUpdate) -> Application:
    app = db.get(Application, application_id)
    if app is None:
        raise ValueError("Application not found")
    if not _application_visible(db, app, user):
        raise PermissionError("Cannot access this application")
    if user.role == UserRole.candidate:
        raise PermissionError("Candidates cannot update application status here")
    if payload.status is not None:
        try:
            app.status = ApplicationStatus(payload.status)
        except ValueError as exc:
            raise ValueError("Invalid application status") from exc
    db.commit()
    db.refresh(app)
    return app


def delete_application(db: Session, application_id: int, user: User) -> None:
    app = db.get(Application, application_id)
    if app is None:
        raise ValueError("Application not found")
    if app.user_id == user.id:
        _delete_application_cascade(db, application_id)
        db.commit()
        return
    if user.role in (UserRole.recruiter, UserRole.admin):
        if not _application_visible(db, app, user):
            raise PermissionError("Cannot delete this application")
        _delete_application_cascade(db, application_id)
        db.commit()
        return
    raise PermissionError("Cannot delete this application")
