import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class AlbumMiddleware(BaseMiddleware):
    """Middleware that collects media-group messages into a single ``album`` list.

    When Telegram sends a media group (album), each photo/video arrives as a
    separate ``Message`` sharing the same ``media_group_id``.  This middleware
    buffers those messages for ``latency`` seconds, then passes the complete
    list to the handler via ``data["album"]``.

    For non-album messages ``data["album"]`` is ``None``.
    """

    def __init__(self, latency: float = 1.0):
        super().__init__()
        self.latency = latency
        self.album_data: Dict[str, list[Message]] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not event.media_group_id:
            data["album"] = None
            return await handler(event, data)

        try:
            self.album_data[event.media_group_id].append(event)
            return  # not the first message — skip handler
        except KeyError:
            self.album_data[event.media_group_id] = [event]
            await asyncio.sleep(self.latency)

        data["album"] = self.album_data.pop(event.media_group_id, [])
        return await handler(event, data)
