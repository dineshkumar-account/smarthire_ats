from datetime import datetime

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    job_id: int


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: int
    user_id: int
    status: str
    resume_text: str | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    status: str | None = None
