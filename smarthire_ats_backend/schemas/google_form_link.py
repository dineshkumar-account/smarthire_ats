from datetime import datetime

from pydantic import BaseModel, HttpUrl


class GoogleFormLinkCreateRequest(BaseModel):
    url: HttpUrl
    job_id: int | None = None
    # Optional if job_id provided. If omitted, company will be derived from job_id.
    company_id: int | None = None
    is_active: bool = True


class GoogleFormLinkUpdateRequest(BaseModel):
    url: HttpUrl | None = None
    is_active: bool | None = None


class GoogleFormLinkRead(BaseModel):
    id: int
    url: str
    company_id: int
    job_id: int | None
    created_by: int
    created_at: datetime
    is_active: bool

    # Extra display fields populated by the service.
    company_name: str | None = None
    job_title: str | None = None

