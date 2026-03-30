from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from models.application import Application
from models.application import ApplicationStatus
from models.application_round import ApplicationRound
from models.company import Company
from models.google_form_link import GoogleFormLink
from models.job import Job
from models.user import User


def get_recruiter_dashboard(db: Session, recruiter_id: int) -> dict:
    companies = db.scalars(select(Company).where(Company.owner_id == recruiter_id)).all()
    company_ids = [c.id for c in companies]
    if not company_ids:
        return {
            "companies_count": 0,
            "jobs_count": 0,
            "applications_count": 0,
            "recent_applications": [],
        }
    jobs_count = db.scalar(select(func.count(Job.id)).where(Job.company_id.in_(company_ids))) or 0
    job_ids_subq = select(Job.id).where(Job.company_id.in_(company_ids))
    applications_count = db.scalar(select(func.count(Application.id)).where(Application.job_id.in_(job_ids_subq))) or 0
    recent = db.scalars(
        select(Application)
        .where(Application.job_id.in_(job_ids_subq))
        .order_by(Application.submitted_at.desc())
        .limit(15)
    ).all()
    recent_payload: list[dict] = []
    for app in recent:
        job = db.get(Job, app.job_id)
        user = app.user
        ats_score = None
        matching_skills = None
        missing_skills = None
        experience_match = None
        if app.ats_analyses:
            latest = max(app.ats_analyses, key=lambda a: a.id)
            ats_score = latest.score
            matching_skills = latest.matching_skills
            missing_skills = latest.missing_skills
            experience_match = latest.experience_match
        recent_payload.append(
            {
                "application_id": app.id,
                "job_id": app.job_id,
                "job_title": job.title if job else None,
                "candidate_name": user.name if user else None,
                "candidate_email": user.email if user else None,
                "status": app.status.value if hasattr(app.status, "value") else str(app.status),
                "ats_score": ats_score,
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "experience_match": experience_match,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            }
        )
    return {
        "companies_count": len(company_ids),
        "jobs_count": int(jobs_count),
        "applications_count": int(applications_count),
        "recent_applications": recent_payload,
    }


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
        "round_number": current.round_number,
        "status": current.status.value if hasattr(current.status, "value") else str(current.status),
        "pinned": bool(current.pinned),
    }


def get_recruiter_applicants(
    db: Session,
    recruiter_id: int,
    job_id: int | None = None,
    *,
    actor_role: str = "recruiter",
) -> dict:
    is_admin = actor_role == "admin"
    jobs_stmt = select(Job).order_by(Job.id.desc())
    if not is_admin:
        jobs_stmt = (
            select(Job)
            .join(Company, Job.company_id == Company.id)
            .where(Company.owner_id == recruiter_id)
            .order_by(Job.id.desc())
        )
    jobs = db.scalars(jobs_stmt).all()
    job_ids = [j.id for j in jobs]
    if job_id is not None and job_id not in job_ids:
        # Safe: recruiter cannot view other recruiters' job applicants.
        jobs = [j for j in jobs if j.id == job_id]
        job_ids = [job_id]

    apps_stmt = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .options(
            selectinload(Application.user),
            selectinload(Application.ats_analyses),
            selectinload(Application.rounds),
        )
        .order_by(Application.submitted_at.desc())
    )
    if not is_admin:
        apps_stmt = apps_stmt.where(Company.owner_id == recruiter_id)
    if job_id is not None:
        apps_stmt = apps_stmt.where(Application.job_id == job_id)
    apps = db.scalars(apps_stmt).all()

    jobs_payload = [{"job_id": j.id, "title": j.title} for j in jobs]

    grouped: dict[str, dict[str, list[dict]]] = {}
    for j in job_ids:
        grouped[str(j)] = {"shortlisted": [], "non_shortlisted": []}

    for app in apps:
        ats = _get_latest_ats(app)
        current_round = _get_current_round(app)

        # If Application.status is missing/unknown, treat as non-shortlisted.
        status_value = app.status.value if hasattr(app.status, "value") else str(app.status)
        shortlisted = status_value == ApplicationStatus.shortlisted.value

        job_key = str(app.job_id)
        if job_key not in grouped:
            grouped[job_key] = {"shortlisted": [], "non_shortlisted": []}

        experience_summary = None
        if ats is None:
            experience_summary = "ATS not analyzed yet"
        else:
            experience_summary = (
                "Experience matches requirements" if ats.get("experience_match") else "Experience does not match requirements"
            )

        applicant_payload = {
            "application_id": app.id,
            "candidate_name": app.user.name if app.user else None,
            "candidate_email": app.user.email if app.user else None,
            "status": status_value,
            "ats_score": ats["score"] if ats else None,
            "matched_skills": ats["matching_skills"] if ats else None,
            "missing_skills": ats["missing_skills"] if ats else None,
            "experience_summary": experience_summary,
            "applied_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "current_round": current_round,
        }

        if shortlisted:
            grouped[job_key]["shortlisted"].append(applicant_payload)
        else:
            grouped[job_key]["non_shortlisted"].append(applicant_payload)

    # Determine selected_job_id for template rendering.
    selected_job_id = job_id
    return {
        "jobs": jobs_payload,
        "selected_job_id": selected_job_id,
        "job_filter": job_id,
        "applicants_by_job": grouped,
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


def _get_company_ids_for_recruiter(db: Session, recruiter_id: int) -> list[int]:
    companies = db.scalars(select(Company.id).where(Company.owner_id == recruiter_id)).all()
    return [int(c) for c in companies]


def get_dashboard_stats(db: Session, recruiter_id: int) -> dict:
    company_ids = _get_company_ids_for_recruiter(db, recruiter_id)
    if not company_ids:
        return {"activeJobs": 0, "newApplicants": 0, "viewedResumes": 0, "googleForms": 0}

    active_jobs = int(
        db.scalar(select(func.count(Job.id)).where(Job.company_id.in_(company_ids), Job.is_active.is_(True))) or 0
    )
    since = datetime.utcnow() - timedelta(days=7)
    job_ids_subq = select(Job.id).where(Job.company_id.in_(company_ids))
    new_applicants = int(
        db.scalar(
            select(func.count(Application.id)).where(Application.job_id.in_(job_ids_subq), Application.submitted_at >= since)
        )
        or 0
    )

    google_forms = int(
        db.scalar(select(func.count(GoogleFormLink.id)).where(GoogleFormLink.company_id.in_(company_ids))) or 0
    )

    # Not implemented yet (no resume view event storage in DB).
    viewed_resumes = 0

    return {
        "activeJobs": active_jobs,
        "newApplicants": new_applicants,
        "viewedResumes": viewed_resumes,
        "googleForms": google_forms,
    }


def get_job_performance(db: Session, recruiter_id: int, days: int = 30) -> dict:
    days = max(7, min(int(days or 30), 90))
    company_ids = _get_company_ids_for_recruiter(db, recruiter_id)
    start = datetime.utcnow() - timedelta(days=days - 1)

    dates: list[str] = []
    applications: list[int] = []
    views: list[int] = []

    if not company_ids:
        for i in range(days):
            d = (start + timedelta(days=i)).date().isoformat()
            dates.append(d)
            applications.append(0)
            views.append(0)
        return {
            "dates": dates,
            "views": views,
            "applications": applications,
            "totalViews": 0,
            "newViews": 0,
            "totalApplications": 0,
            "newApplications": 0,
        }

    job_ids_subq = select(Job.id).where(Job.company_id.in_(company_ids))
    # Counts by date (UTC date).
    rows = db.execute(
        select(func.date(Application.submitted_at), func.count(Application.id))
        .where(Application.job_id.in_(job_ids_subq), Application.submitted_at >= start)
        .group_by(func.date(Application.submitted_at))
    ).all()
    by_date = {str(r[0]): int(r[1]) for r in rows if r[0] is not None}

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


def get_applicant_stages(db: Session, recruiter_id: int) -> dict:
    company_ids = _get_company_ids_for_recruiter(db, recruiter_id)
    if not company_ids:
        return {
            "shortlisted": 0,
            "interviewing": 0,
            "underReview": 0,
            "rejected": 0,
            "recentActivity": [],
        }

    job_ids_subq = select(Job.id).where(Job.company_id.in_(company_ids))
    apps = db.scalars(
        select(Application)
        .where(Application.job_id.in_(job_ids_subq))
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
        # applied or unknown
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


def get_google_forms_recent(db: Session, recruiter_id: int) -> dict:
    company_ids = _get_company_ids_for_recruiter(db, recruiter_id)
    if not company_ids:
        return {"forms": [], "recentSubmissions": []}

    links = db.scalars(
        select(GoogleFormLink)
        .where(GoogleFormLink.company_id.in_(company_ids))
        .order_by(GoogleFormLink.created_at.desc())
        .limit(25)
    ).all()
    forms_payload: list[dict] = []
    for l in links:
        job = db.get(Job, l.job_id) if l.job_id else None
        forms_payload.append({"id": l.id, "name": f"Form #{l.id}", "linkedJob": job.title if job else None})

    # Submissions are not stored yet.
    return {"forms": forms_payload, "recentSubmissions": []}
