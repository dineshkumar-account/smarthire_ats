from pydantic import BaseModel


class AtsAnalysisBase(BaseModel):
    application_id: int
    score: float
    matching_skills: list | dict | None = None
    missing_skills: list | dict | None = None
    experience_match: bool = False


class AtsAnalysisRead(AtsAnalysisBase):
    id: int

    model_config = {"from_attributes": True}
