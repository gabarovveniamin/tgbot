import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Admin(Base):
    """Administrator record. Only one admin is registered at first launch."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
