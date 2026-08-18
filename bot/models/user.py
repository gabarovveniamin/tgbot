import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    """Bot user who can submit content for the channel."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    anonymous_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    submissions = relationship("Submission", back_populates="user", lazy="selectin")
