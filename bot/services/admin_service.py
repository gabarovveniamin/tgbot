from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.admin import Admin


class AdminService:
    """Service layer for admin-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_admin(self) -> Admin | None:
        """Get the single registered admin (if any)."""
        result = await self.session.execute(select(Admin).limit(1))
        return result.scalar_one_or_none()

    async def register_admin(self, telegram_id: int) -> Admin | None:
        """Register the first admin. Returns None if an admin already exists."""
        existing = await self.get_admin()
        if existing:
            return None
        admin = Admin(telegram_id=telegram_id)
        self.session.add(admin)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            return None
        await self.session.refresh(admin)
        return admin

    async def is_admin(self, telegram_id: int) -> bool:
        """Check whether a given telegram_id belongs to the admin."""
        result = await self.session.execute(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none() is not None
