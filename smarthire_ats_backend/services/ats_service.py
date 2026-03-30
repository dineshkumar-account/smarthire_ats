import os

from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatus
from models.ats_analysis import AtsAnalysis
from models.company import Company
from models.job import Job
from models.user import User, UserRole
from nlp.resume_parser import extract_resume_skills_experience


def _can_analyze(db: Session, app: Application, actor: User) -> bool:
    if app.user_id == actor.id:
        return True
    if actor.role == UserRole.admin:
        return True
    if actor.role != UserRole.recruiter:
        return False
    job = db.get(Job, app.job_id)
    if job is None:
        return False
    company = db.get(Company, job.company_id)
    return company is not None and company.owner_id == actor.id


def analyze_application(db: Session, application_id: int, actor: User) -> AtsAnalysis:
    app = db.get(Application, application_id)
    if app is None:
        raise ValueError("Application not found")
    if not _can_analyze(db, app, actor):
        raise PermissionError("Not allowed to analyze this application")
    job = db.get(Job, app.job_id)
    if job is None:
        raise ValueError("Job not found")
    resume_text = app.resume_text or ""
    result = extract_resume_skills_experience(resume_text, job.skills_required)

    # Shortlist based on configurable threshold.
    # If candidate score >= threshold => shortlisted, else rejected.
    threshold = float(os.getenv("ATS_SHORTLIST_THRESHOLD", "60"))
    score_value = float(result.get("score", 0))
    app.status = ApplicationStatus.shortlisted if score_value >= threshold else ApplicationStatus.rejected

    for row in list(app.ats_analyses):
        db.delete(row)
    analysis = AtsAnalysis(
        application_id=app.id,
        score=score_value,
        matching_skills=result.get("matching_skills"),
        missing_skills=result.get("missing_skills"),
        experience_match=bool(result.get("experience_match", False)),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
