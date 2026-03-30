from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from services import company_service
from utils.service_errors import raise_service_exception

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    try:
        company = company_service.create_company(db, current_user.id, payload)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return CompanyRead.model_validate(company)


@router.get("", response_model=list[CompanyRead])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CompanyRead]:
    companies = company_service.list_companies(db, current_user)
    return [CompanyRead.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    company = company_service.get_company(db, company_id, current_user)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyRead.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyRead:
    try:
        company = company_service.update_company(db, company_id, payload, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
    return CompanyRead.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        company_service.delete_company(db, company_id, current_user)
    except (ValueError, PermissionError) as e:
        raise_service_exception(e)
