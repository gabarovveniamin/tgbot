import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Submission(Base):
    """A user's content submission. Status: pending / published / rejected."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("User", back_populates="submissions", lazy="selectin")
    media_items = relationship("Media", back_populates="submission", lazy="selectin")
