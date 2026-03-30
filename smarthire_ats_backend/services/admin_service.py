from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from models.application import Application, ApplicationStatus
from models.company import Company
from models.google_form_link import GoogleFormLink
from models.job import Job
from models.ats_analysis import AtsAnalysis
from models.application_round import ApplicationRound
from models.user import User, UserRole
from utils.hash import get_password_hash


def list_users_by_roles(db: Session, roles: list[UserRole] | None = None) -> list[User]:
    stmt = select(User)
    if roles:
        stmt = stmt.where(User.role.in_(roles))
    stmt = stmt.order_by(User.created_at.desc())
    return list(db.scalars(stmt).all())


def reset_user_password(db: Session, user_id: int, expected_role: UserRole, new_password: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    if user.role != expected_role:
        raise ValueError("Role mismatch for user")
    if not isinstance(new_password, str) or len(new_password.strip()) < 4:
        raise ValueError("Password must be at least 4 characters")
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_recruiter(db: Session, payload: dict) -> User:
    email = payload["email"].lower().strip()
    if db.scalars(select(User).where(User.email == email)).first():
        raise ValueError("Email already registered")
    user = User(
        email=email,
        password_hash=get_password_hash(payload["password"]),
        name=payload["name"].strip(),
        role=UserRole.recruiter,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin(db: Session, payload: dict) -> User:
    email = payload["email"].lower().strip()
    if db.scalars(select(User).where(User.email == email)).first():
        raise ValueError("Email already registered")
    user = User(
        email=email,
        password_hash=get_password_hash(payload["password"]),
        name=payload["name"].strip(),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_admin_dashboard(db: Session) -> dict:
    users = db.scalars(select(User)).all()
    by_role: dict[str, int] = {r.value: 0 for r in UserRole}
    for u in users:
        by_role[u.role.value] = by_role.get(u.role.value, 0) + 1
    companies_count = int(db.scalar(select(func.count(Company.id))) or 0)
    jobs_count = int(db.scalar(select(func.count(Job.id))) or 0)
    applications_count = int(db.scalar(select(func.count(Application.id))) or 0)
    return {
        "total_users": len(users),
        "users_by_role": by_role,
        "companies_count": companies_count,
        "jobs_count": jobs_count,
        "applications_count": applications_count,
    }


def list_companies_admin(db: Session) -> list[Company]:
    return list(db.scalars(select(Company).order_by(Company.id)).all())


def _get_latest_ats(app: Application) -> dict | None:
    if not app.ats_analyses:
        return None
    latest = max(app.ats_analyses, key=lambda a: a.id)
    return {
        "score": float(latest.score),
        "matching_skills": latest.matching_skills,
        "missing_skills": latest.missing_skills,
        "experience_match": bool(latest.experience_match),
    }


def _get_current_round(app: Application) -> dict | None:
    if not app.rounds:
        return None
    pinned_round = next((r for r in app.rounds if r.pinned), None)
    current = pinned_round if pinned_round else max(app.rounds, key=lambda r: r.round_number)
    return {
        "round_number": int(current.round_number),
        "status": current.status.value if hasattr(current.status, "value") else str(current.status),
        "pinned": bool(current.pinned),
    }


def get_admin_applicants(db: Session, admin_id: int) -> dict:
    # admin_id is not needed for scoping (admins see all),
    # but kept for future consistency.
    stmt = (
        select(Application)
        .options(
            selectinload(Application.user),
            selectinload(Application.ats_analyses),
            selectinload(Application.rounds),
            selectinload(Application.job).selectinload(Job.company).selectinload(Company.owner),
        )
        .order_by(Application.submitted_at.desc())
    )
    apps = db.scalars(stmt).all()

    jobs_map: dict[int, dict] = {}
    applicants_by_job: dict[int, dict[str, list[dict]]] = {}

    for app in apps:
        job = app.job
        if job is None:
            continue
        company = job.company
        recruiter = company.owner if company else None

        if job.id not in jobs_map:
            jobs_map[job.id] = {
                "job_id": job.id,
                "title": job.title,
                "company_name": company.name if company else None,
                "recruiter_name": recruiter.name if recruiter else None,
                "recruiter_email": recruiter.email if recruiter else None,
            }
            applicants_by_job[job.id] = {"shortlisted": [], "non_shortlisted": []}

        status_value = app.status.value if hasattr(app.status, "value") else str(app.status)
        is_shortlisted = status_value == ApplicationStatus.shortlisted.value

        latest_ats = _get_latest_ats(app)
        if latest_ats is None:
            ats_score = None
            matched_skills = None
            missing_skills = None
            experience_summary = "ATS not analyzed yet"
        else:
            ats_score = latest_ats["score"]
            matched_skills = latest_ats["matching_skills"]
            missing_skills = latest_ats["missing_skills"]
            experience_summary = (
                "Experience matches requirements" if latest_ats["experience_match"] else "Experience does not match requirements"
            )

        current_round = _get_current_round(app)

        applicant_payload = {
            "application_id": app.id,
            "candidate_name": app.user.name if app.user else None,
            "candidate_email": app.user.email if app.user else None,
            "status": status_value,
            "ats_score": ats_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "experience_summary": experience_summary,
            "applied_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "current_round": current_round,
        }

        if is_shortlisted:
            applicants_by_job[job.id]["shortlisted"].append(applicant_payload)
        else:
            applicants_by_job[job.id]["non_shortlisted"].append(applicant_payload)

    jobs_payload = [jobs_map[jid] for jid in sorted(jobs_map.keys(), reverse=True)]
    applicants_by_job_payload = {str(jid): v for jid, v in applicants_by_job.items()}

    return {
        "jobs": jobs_payload,
        "applicants_by_job": applicants_by_job_payload,
    }


def get_admin_recruiter_dashboard(db: Session) -> dict:
    companies_count = int(db.scalar(select(func.count(Company.id))) or 0)
    jobs_count = int(db.scalar(select(func.count(Job.id))) or 0)
    applications_count = int(db.scalar(select(func.count(Application.id))) or 0)

    stmt = (
        select(Application)
        .options(selectinload(Application.user))
        .order_by(Application.submitted_at.desc())
        .limit(15)
    )
    recent = db.scalars(stmt).all()
    recent_payload: list[dict] = []
    for app in recent:
        job = db.get(Job, app.job_id)
        user = app.user
        ats_score = None
        if app.ats_analyses:
            latest = max(app.ats_analyses, key=lambda a: a.id)
            ats_score = latest.score
        recent_payload.append(
            {
                "application_id": app.id,
                "job_id": app.job_id,
                "job_title": job.title if job else None,
                "candidate_name": user.name if user else None,
                "candidate_email": user.email if user else None,
                "status": app.status.value if hasattr(app.status, "value") else str(app.status),
                "ats_score": ats_score,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            }
        )
    return {
        "companies_count": companies_count,
        "jobs_count": jobs_count,
        "applications_count": applications_count,
        "recent_applications": recent_payload,
    }


def _time_ago(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{max(1, seconds)}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def get_admin_recruiter_dashboard_stats(db: Session) -> dict:
    active_jobs = int(db.scalar(select(func.count(Job.id)).where(Job.is_active.is_(True))) or 0)
    since = datetime.utcnow() - timedelta(days=7)
    new_applicants = int(db.scalar(select(func.count(Application.id)).where(Application.submitted_at >= since)) or 0)
    google_forms = int(db.scalar(select(func.count(GoogleFormLink.id))) or 0)
    viewed_resumes = 0  # not tracked yet
    return {
        "activeJobs": active_jobs,
        "newApplicants": new_applicants,
        "viewedResumes": viewed_resumes,
        "googleForms": google_forms,
    }


def get_admin_recruiter_job_performance(db: Session, days: int = 30) -> dict:
    days = max(7, min(int(days or 30), 90))
    start = datetime.utcnow() - timedelta(days=days - 1)
    rows = db.execute(
        select(func.date(Application.submitted_at), func.count(Application.id))
        .where(Application.submitted_at >= start)
        .group_by(func.date(Application.submitted_at))
    ).all()
    by_date = {str(r[0]): int(r[1]) for r in rows if r[0] is not None}

    dates: list[str] = []
    applications: list[int] = []
    views: list[int] = []
    total_applications = 0
    for i in range(days):
        d = (start + timedelta(days=i)).date().isoformat()
        dates.append(d)
        c = int(by_date.get(d, 0))
        applications.append(c)
        total_applications += c
        views.append(0)  # not tracked yet
    new_applications = sum(applications[-7:]) if len(applications) >= 7 else total_applications

    return {
        "dates": dates,
        "views": views,
        "applications": applications,
        "totalViews": 0,
        "newViews": 0,
        "totalApplications": total_applications,
        "newApplications": new_applications,
    }


def get_admin_recruiter_applicant_stages(db: Session) -> dict:
    apps = db.scalars(
        select(Application)
        .options(selectinload(Application.user))
        .order_by(Application.submitted_at.desc())
        .limit(50)
    ).all()
    counts = {"shortlisted": 0, "interviewing": 0, "underReview": 0, "rejected": 0}
    recent_activity: list[dict] = []

    def map_stage(status: str) -> str:
        if status == ApplicationStatus.shortlisted.value:
            return "shortlisted"
        if status == ApplicationStatus.rejected.value:
            return "rejected"
        if status == ApplicationStatus.in_progress.value:
            return "interviewing"
        return "underReview"

    for app in apps:
        status_value = app.status.value if hasattr(app.status, "value") else str(app.status)
        stage = map_stage(status_value)
        counts[stage] += 1
        if len(recent_activity) < 6:
            recent_activity.append(
                {
                    "name": (app.user.name if app.user else None) or "Candidate",
                    "stage": stage,
                    "timeAgo": _time_ago(app.submitted_at),
                }
            )

    return {
        "shortlisted": counts["shortlisted"],
        "interviewing": counts["interviewing"],
        "underReview": counts["underReview"],
        "rejected": counts["rejected"],
        "recentActivity": recent_activity,
    }


def get_admin_recruiter_google_forms_recent(db: Session) -> dict:
    links = db.scalars(select(GoogleFormLink).order_by(GoogleFormLink.created_at.desc()).limit(25)).all()
    forms_payload: list[dict] = []
    for l in links:
        job = db.get(Job, l.job_id) if l.job_id else None
        forms_payload.append({"id": l.id, "name": f"Form #{l.id}", "linkedJob": job.title if job else None})
    return {"forms": forms_payload, "recentSubmissions": []}


def get_admin_candidate_dashboard_registered(db: Session) -> list[dict]:
    """
    Registered candidates: candidate users who submitted applications in the portal.
    """
    stmt = (
        select(Application)
        .join(User, Application.user_id == User.id)
        .options(selectinload(Application.user))
        .order_by(Application.submitted_at.desc())
    )
    apps = db.scalars(stmt).all()
    payload: list[dict] = []
    for app in apps:
        if app.user is None or app.user.role != UserRole.candidate:
            continue
        job = db.get(Job, app.job_id)
        payload.append(
            {
                "candidate_name": app.user.name,
                "candidate_email": app.user.email,
                "job_id": app.job_id,
                "job_title": job.title if job else None,
                "applied_at": app.submitted_at.isoformat() if app.submitted_at else None,
                "status": app.status.value if hasattr(app.status, "value") else str(app.status),
                "application_id": app.id,
            }
        )
    return payload


def get_admin_candidate_dashboard_google_form(db: Session) -> list[dict]:
    """
    Placeholder: the project currently stores Google Form links but not submissions.
    Returns empty list until a Google Form submission ingestion pipeline is added.
    """
    _ = db
    return []
