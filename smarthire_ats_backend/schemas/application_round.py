from pydantic import BaseModel


class ApplicationRoundBase(BaseModel):
    application_id: int
    round_number: int
    status: str
    pinned: bool = False
    notes: str | None = None


class ApplicationRoundRead(ApplicationRoundBase):
    id: int

    model_config = {"from_attributes": True}


class ApplicationRoundUpdate(BaseModel):
    status: str | None = None
    pinned: bool | None = None
    notes: str | None = None


class ApplicationRoundUpsertRequest(BaseModel):
    round_number: int
    status: str
    pinned: bool = False
    notes: str | None = None
