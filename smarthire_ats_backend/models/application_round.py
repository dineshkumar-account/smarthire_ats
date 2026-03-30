import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class RoundStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    passed = "passed"
    failed = "failed"


class ApplicationRound(Base):
    __tablename__ = "application_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RoundStatus] = mapped_column(Enum(RoundStatus), default=RoundStatus.todo, nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="rounds")
