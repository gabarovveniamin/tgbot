from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserService:
    """Service layer for user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self, telegram_id: int, username: str | None, full_name: str | None
    ) -> User:
        """Get an existing user or create a new one. Always updates username/full_name."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            user.full_name = full_name
            await self.session.commit()
            return user
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            anonymous_mode=False,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_anonymous_mode(self, telegram_id: int, anonymous: bool) -> None:
        """Toggle anonymous mode for the given user."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.anonymous_mode = anonymous
            await self.session.commit()

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
