from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.models.base import Base


class DatabaseEngine:
    """Async SQLite database engine and session factory."""

    def __init__(self, db_url: str = "sqlite+aiosqlite:///bot.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        """Create all tables defined in models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Dispose the engine connection pool."""
        await self.engine.dispose()
