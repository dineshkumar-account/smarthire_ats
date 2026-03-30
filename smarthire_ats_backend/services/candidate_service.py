from sqlalchemy import select
from sqlalchemy.orm import Session

from models.application import Application
from models.application import ApplicationStatus
from models.company import Company
from models.job import Job


def get_candidate_dashboard(db: Session, candidate_id: int) -> dict:
    apps = db.scalars(
        select(Application).where(Application.user_id == candidate_id).order_by(Application.submitted_at.desc())
    ).all()
    rows: list[dict] = []
    shortlisted = False
    shortlisted_company_ids: set[int] = set()
    for app in apps:
        job = db.get(Job, app.job_id)
        score = None
        matching_skills = None
        missing_skills = None
        experience_match = None

        if app.ats_analyses:
            latest = max(app.ats_analyses, key=lambda a: a.id)
            score = latest.score
            matching_skills = latest.matching_skills
            missing_skills = latest.missing_skills
            experience_match = latest.experience_match

        company_name = None
        if job:
            co = db.get(Company, job.company_id)
            company_name = co.name if co else None

        status_value = app.status.value if hasattr(app.status, "value") else str(app.status)
        if status_value == ApplicationStatus.shortlisted.value:
            shortlisted = True
            if job:
                shortlisted_company_ids.add(job.company_id)

        rows.append(
            {
                "application_id": app.id,
                "job_id": app.job_id,
                "job_title": job.title if job else None,
                "company_name": company_name,
                "status": status_value,
                "ats_score": score,
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "experience_match": experience_match,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            }
        )

    payload: dict = {"applications": rows, "shortlisted": shortlisted}

    if shortlisted and shortlisted_company_ids:
        available_jobs = db.scalars(
            select(Job)
            .where(Job.company_id.in_(list(shortlisted_company_ids)), Job.is_active.is_(True))
            .order_by(Job.id.desc())
            .limit(10)
        ).all()
        payload["available_jobs"] = [{"job_id": j.id, "title": j.title} for j in available_jobs]
    return payload
