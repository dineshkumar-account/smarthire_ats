from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.application import Application
from models.application_round import ApplicationRound, RoundStatus
from models.company import Company
from models.job import Job
from models.user import User, UserRole

from schemas.application_round import ApplicationRoundRead, ApplicationRoundUpsertRequest


def _can_manage_application_round(db: Session, application_id: int, actor: User) -> bool:
    if actor.role == UserRole.admin:
        return True

    app = db.get(Application, application_id)
    if app is None:
        return False

    job = db.get(Job, app.job_id)
    if job is None:
        return False

    company = db.get(Company, job.company_id)
    if company is None:
        return False

    return company.owner_id == actor.id


def list_rounds_for_application(db: Session, application_id: int, actor: User) -> list[ApplicationRoundRead]:
    if not _can_manage_application_round(db, application_id, actor):
        raise PermissionError("Not allowed to access rounds for this application")

    rounds = list(
        db.scalars(
            select(ApplicationRound).where(ApplicationRound.application_id == application_id).order_by(ApplicationRound.round_number)
        ).all()
    )
    return [ApplicationRoundRead.model_validate(r) for r in rounds]


def upsert_round(
    db: Session,
    application_id: int,
    actor: User,
    payload: ApplicationRoundUpsertRequest,
) -> ApplicationRoundRead:
    if not _can_manage_application_round(db, application_id, actor):
        raise PermissionError("Not allowed to modify rounds for this application")

    try:
        status_enum = RoundStatus(payload.status)
    except ValueError as exc:
        raise ValueError("Invalid round status") from exc

    existing = db.scalars(
        select(ApplicationRound).where(
            ApplicationRound.application_id == application_id,
            ApplicationRound.round_number == payload.round_number,
        )
    ).first()

    pinned_target = bool(payload.pinned)

    if pinned_target:
        # Enforce at most one pinned round per application.
        db.execute(
            update(ApplicationRound).where(ApplicationRound.application_id == application_id).values(pinned=False)
        )
        db.commit()

    if existing is not None:
        existing.status = status_enum
        existing.notes = payload.notes
        existing.pinned = pinned_target
        db.commit()
        db.refresh(existing)
        return ApplicationRoundRead.model_validate(existing)

    new_round = ApplicationRound(
        application_id=application_id,
        round_number=payload.round_number,
        status=status_enum,
        pinned=pinned_target,
        notes=payload.notes,
    )
    db.add(new_round)
    db.commit()
    db.refresh(new_round)
    return ApplicationRoundRead.model_validate(new_round)


def delete_round(db: Session, round_id: int, actor: User) -> None:
    round_row = db.get(ApplicationRound, round_id)
    if round_row is None:
        raise ValueError("Round not found")

    if not _can_manage_application_round(db, round_row.application_id, actor):
        raise PermissionError("Not allowed to delete this round")

    db.delete(round_row)
    db.commit()

