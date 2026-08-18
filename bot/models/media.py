from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Media(Base):
    """A single media item attached to a submission."""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id"), nullable=False
    )
    file_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission = relationship("Submission", back_populates="media_items")
