from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None


class CompanyRead(CompanyBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
