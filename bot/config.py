from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    bot_token: str
    channel_id: int

    @staticmethod
    def load() -> "Config":
        token = getenv("BOT_TOKEN")
        channel = getenv("CHANNEL_ID")
        if not token:
            raise ValueError("BOT_TOKEN is not set in .env")
        if not channel:
            raise ValueError("CHANNEL_ID is not set in .env")
        return Config(
            bot_token=token,
            channel_id=int(channel),
        )
