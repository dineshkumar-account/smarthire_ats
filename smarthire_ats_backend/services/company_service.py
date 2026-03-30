from sqlalchemy import select
from sqlalchemy.orm import Session

from models.company import Company
from models.user import User, UserRole
from schemas.company import CompanyCreate, CompanyUpdate
from services.job_service import delete_job_cascade


def create_company(db: Session, owner_id: int, payload: CompanyCreate) -> Company:
    owner = db.get(User, owner_id)
    if owner is None:
        raise ValueError("Owner not found")
    if owner.role not in (UserRole.recruiter, UserRole.admin):
        raise PermissionError("Only recruiters or admins can create companies")
    company = Company(name=payload.name.strip(), owner_id=owner_id)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_company(db: Session, company_id: int, user: User) -> Company | None:
    company = db.get(Company, company_id)
    if company is None:
        return None
    if user.role == UserRole.admin:
        return company
    if company.owner_id == user.id:
        return company
    return None


def list_companies(db: Session, user: User) -> list[Company]:
    if user.role == UserRole.admin:
        return list(db.scalars(select(Company).order_by(Company.id)).all())
    return list(db.scalars(select(Company).where(Company.owner_id == user.id).order_by(Company.id)).all())


def update_company(db: Session, company_id: int, payload: CompanyUpdate, actor: User) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError("Company not found")
    if company.owner_id != actor.id and actor.role != UserRole.admin:
        raise PermissionError("Not allowed to update this company")
    if payload.name is not None:
        company.name = payload.name.strip()
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company_id: int, actor: User) -> None:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError("Company not found")
    if company.owner_id != actor.id and actor.role != UserRole.admin:
        raise PermissionError("Not allowed to delete this company")
    from models.job import Job

    jobs = db.scalars(select(Job).where(Job.company_id == company_id)).all()
    for job in jobs:
        delete_job_cascade(db, job.id)
    db.delete(company)
    db.commit()
