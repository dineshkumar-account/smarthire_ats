from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class AtsAnalysis(Base):
    __tablename__ = "ats_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    matching_skills: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    experience_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application = relationship("Application", back_populates="ats_analyses")
