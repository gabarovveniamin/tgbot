"""Entry point — configure bot, database, middleware, routers and start polling."""

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import Config
from bot.database import DatabaseEngine
from bot.handlers import admin, submissions, user
from bot.utils.album_middleware import AlbumMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    )
    logger = logging.getLogger(__name__)

    config = Config.load()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # ── Database ─────────────────────────────────────────────────────────
    db = DatabaseEngine()
    await db.create_tables()
    dp["db"] = db

    # ── Middleware ────────────────────────────────────────────────────────
    dp.message.middleware(AlbumMiddleware(latency=1.0))

    # ── Routers (order matters — admin FSM first) ────────────────────────
    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.include_router(submissions.router)

    # ── Polling ──────────────────────────────────────────────────────────
    try:
        logger.info("Bot started — polling…")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down…")
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
