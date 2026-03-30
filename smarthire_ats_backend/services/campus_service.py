import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatus
from models.job import Job
from models.user import User, UserRole
from utils.hash import get_password_hash


def import_candidates_from_csv(db: Session, file_bytes: bytes) -> dict:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    required = {"email", "name", "job_id"}
    if not required.issubset(set(fieldnames)):
        raise ValueError(f"CSV must include columns: {sorted(required)}")
    created_users = 0
    created_applications = 0
    skipped = 0
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            email = row["email"].lower().strip()
            name = row["name"].strip()
            job_id = int(row["job_id"])
            password = (row.get("password") or "").strip() or "changeme123"
            job = db.get(Job, job_id)
            if job is None or not job.is_active:
                errors.append(f"Row {i}: invalid or inactive job_id {job_id}")
                continue
            user = db.scalars(select(User).where(User.email == email)).first()
            if user is None:
                user = User(
                    email=email,
                    password_hash=get_password_hash(password),
                    name=name,
                    role=UserRole.candidate,
                )
                db.add(user)
                db.flush()
                created_users += 1
            elif user.role != UserRole.candidate:
                errors.append(f"Row {i}: email {email} exists with non-candidate role")
                continue
            dup = db.scalars(
                select(Application).where(Application.user_id == user.id, Application.job_id == job_id)
            ).first()
            if dup:
                skipped += 1
                continue
            app = Application(
                user_id=user.id,
                job_id=job_id,
                resume_text=None,
                status=ApplicationStatus.applied,
            )
            db.add(app)
            created_applications += 1
        except Exception as e:
            errors.append(f"Row {i}: {e!s}")
    db.commit()
    return {
        "created_users": created_users,
        "created_applications": created_applications,
        "skipped_duplicate_applications": skipped,
        "errors": errors,
    }
