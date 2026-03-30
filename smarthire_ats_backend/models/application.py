import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    shortlisted = "shortlisted"
    rejected = "rejected"
    in_progress = "in_progress"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.applied, nullable=False
    )
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    ats_analyses = relationship("AtsAnalysis", back_populates="application")
    rounds = relationship("ApplicationRound", back_populates="application")
