from datetime import datetime

from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    description: str
    skills_required: str
    experience_min: int = 0


class JobCreate(JobBase):
    company_id: int


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    skills_required: str | None = None
    experience_min: int | None = None
    is_active: bool | None = None


class JobRead(JobBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
