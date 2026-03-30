from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.company import Company
from models.google_form_link import GoogleFormLink
from models.job import Job
from models.user import User, UserRole
from schemas.google_form_link import (
    GoogleFormLinkCreateRequest,
    GoogleFormLinkRead,
    GoogleFormLinkUpdateRequest,
)


def _can_manage_company(db: Session, company_id: int, actor: User) -> bool:
    if actor.role == UserRole.admin:
        return True
    company = db.get(Company, company_id)
    return company is not None and company.owner_id == actor.id


def _derive_company_and_job_ids(db: Session, actor: User, payload: GoogleFormLinkCreateRequest) -> tuple[int, int | None]:
    job_id = payload.job_id
    if job_id is not None:
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError("Job not found")
        company_id = job.company_id
    else:
        if payload.company_id is None:
            raise ValueError("Either job_id or company_id must be provided")
        company_id = payload.company_id

    if not _can_manage_company(db, company_id, actor):
        raise PermissionError("Not allowed to create links for this company")

    return company_id, job_id


def list_google_form_links(db: Session, actor: User) -> list[GoogleFormLinkRead]:
    stmt = select(GoogleFormLink).options(
        selectinload(GoogleFormLink.company),
        selectinload(GoogleFormLink.job),
    )
    if actor.role != UserRole.admin:
        stmt = stmt.join(Company, GoogleFormLink.company_id == Company.id).where(Company.owner_id == actor.id)

    stmt = stmt.order_by(GoogleFormLink.id.desc())
    rows = list(db.scalars(stmt).all())

    payload: list[GoogleFormLinkRead] = []
    for row in rows:
        payload.append(
            GoogleFormLinkRead(
                id=row.id,
                url=row.url,
                company_id=row.company_id,
                job_id=row.job_id,
                created_by=row.created_by,
                created_at=row.created_at,
                is_active=row.is_active,
                company_name=row.company.name if row.company else None,
                job_title=row.job.title if row.job else None,
            )
        )
    return payload


def create_google_form_link(db: Session, actor: User, payload: GoogleFormLinkCreateRequest) -> GoogleFormLinkRead:
    company_id, job_id = _derive_company_and_job_ids(db, actor, payload)

    link = GoogleFormLink(
        url=payload.url.strip(),
        company_id=company_id,
        job_id=job_id,
        created_by=actor.id,
        is_active=payload.is_active,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    # Enrich display fields.
    company = db.get(Company, company_id)
    job = db.get(Job, job_id) if job_id is not None else None
    return GoogleFormLinkRead(
        id=link.id,
        url=link.url,
        company_id=link.company_id,
        job_id=link.job_id,
        created_by=link.created_by,
        created_at=link.created_at,
        is_active=link.is_active,
        company_name=company.name if company else None,
        job_title=job.title if job else None,
    )


def update_google_form_link(
    db: Session,
    actor: User,
    link_id: int,
    payload: GoogleFormLinkUpdateRequest,
) -> GoogleFormLinkRead:
    link = db.get(GoogleFormLink, link_id)
    if link is None:
        raise ValueError("Link not found")

    if not _can_manage_company(db, link.company_id, actor):
        raise PermissionError("Not allowed to update this link")

    if payload.url is not None:
        link.url = payload.url.strip()
    if payload.is_active is not None:
        link.is_active = payload.is_active

    db.commit()
    db.refresh(link)

    company = db.get(Company, link.company_id)
    job = db.get(Job, link.job_id) if link.job_id is not None else None
    return GoogleFormLinkRead(
        id=link.id,
        url=link.url,
        company_id=link.company_id,
        job_id=link.job_id,
        created_by=link.created_by,
        created_at=link.created_at,
        is_active=link.is_active,
        company_name=company.name if company else None,
        job_title=job.title if job else None,
    )


def delete_google_form_link(db: Session, actor: User, link_id: int) -> None:
    link = db.get(GoogleFormLink, link_id)
    if link is None:
        raise ValueError("Link not found")
    if not _can_manage_company(db, link.company_id, actor):
        raise PermissionError("Not allowed to delete this link")

    db.delete(link)
    db.commit()

