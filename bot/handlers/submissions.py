"""Content submission flow: receive content → save → notify admin.

Shared helpers for sending / copying content are also defined here so that
the admin handler can reuse them when publishing to the channel.
"""

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from bot.database import DatabaseEngine
from bot.keyboards import main_menu_keyboard
from bot.keyboards.inline import admin_submission_keyboard
from bot.services import AdminService, SubmissionService, UserService
from bot.states import UserStates
from bot.utils import check_spam

router = Router()

# ── Constants ────────────────────────────────────────────────────────────────

MEDIA_TYPE_NAMES: dict[str, str] = {
    "text": "📝 Текст",
    "photo": "🖼 Фотография",
    "video": "🎬 Видео",
    "animation": "🎞 GIF-анимация",
    "sticker": "🎨 Стикер",
    "voice": "🎤 Голосовое сообщение",
    "video_note": "📹 Видеосообщение",
    "audio": "🎵 Аудио",
    "document": "📄 Документ",
    "media_group": "📎 Альбом",
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def detect_media(message: Message) -> tuple[str, str, str | None]:
    """Return ``(media_type, file_id, caption)`` for a single message."""
    if message.photo:
        return "photo", message.photo[-1].file_id, message.caption
    if message.video:
        return "video", message.video.file_id, message.caption
    if message.animation:
        return "animation", message.animation.file_id, message.caption
    if message.sticker:
        return "sticker", message.sticker.file_id, None
    if message.voice:
        return "voice", message.voice.file_id, message.caption
    if message.video_note:
        return "video_note", message.video_note.file_id, None
    if message.audio:
        return "audio", message.audio.file_id, message.caption
    if message.document:
        return "document", message.document.file_id, message.caption
    if message.text:
        return "text", "", message.text
    return "unknown", "", None


async def send_single_media(
    bot: Bot,
    chat_id: int,
    media_type: str,
    file_id: str,
    caption: str | None = None,
) -> None:
    """Copy a single media item to *chat_id* (no forward, fresh message)."""
    if media_type == "text":
        await bot.send_message(chat_id, caption or "")
    elif media_type == "photo":
        await bot.send_photo(chat_id, file_id, caption=caption)
    elif media_type == "video":
        await bot.send_video(chat_id, file_id, caption=caption)
    elif media_type == "animation":
        await bot.send_animation(chat_id, file_id, caption=caption)
    elif media_type == "sticker":
        await bot.send_sticker(chat_id, file_id)
    elif media_type == "voice":
        await bot.send_voice(chat_id, file_id, caption=caption)
    elif media_type == "video_note":
        await bot.send_video_note(chat_id, file_id)
    elif media_type == "audio":
        await bot.send_audio(chat_id, file_id, caption=caption)
    elif media_type == "document":
        await bot.send_document(chat_id, file_id, caption=caption)


async def send_media_group_items(
    bot: Bot,
    chat_id: int,
    media_items: list,
    extra_caption: str = "",
) -> None:
    """Send a list of ``Media`` DB rows as a Telegram media group."""
    input_media = []
    for i, item in enumerate(media_items):
        cap = None
        if i == 0:
            base = item.caption or ""
            combined = (base + extra_caption).strip() if (base or extra_caption) else ""
            cap = combined or None

        if item.media_type == "photo":
            input_media.append(InputMediaPhoto(media=item.file_id, caption=cap))
        elif item.media_type == "video":
            input_media.append(InputMediaVideo(media=item.file_id, caption=cap))
        elif item.media_type == "audio":
            input_media.append(InputMediaAudio(media=item.file_id, caption=cap))
        elif item.media_type == "document":
            input_media.append(InputMediaDocument(media=item.file_id, caption=cap))

    if input_media:
        await bot.send_media_group(chat_id, input_media)


async def notify_admin(bot: Bot, db: DatabaseEngine, submission_id: int) -> None:
    """Build the info card + content copy and send to admin."""
    async with db.session_factory() as session:
        submission_service = SubmissionService(session)
        submission = await submission_service.get_submission(submission_id)
        if not submission:
            return

        user_service = UserService(session)
        user = await user_service.get_user_by_id(submission.user_id)
        if not user:
            return

        admin_service = AdminService(session)
        admin = await admin_service.get_admin()
        if not admin:
            return

        media_items = submission.media_items
        if not media_items:
            return

        # ── info text ────────────────────────────────────────────────────
        created_at = (
            submission.created_at.strftime("%d.%m.%Y %H:%M")
            if submission.created_at
            else "—"
        )

        type_name = (
            MEDIA_TYPE_NAMES.get(media_items[0].media_type, "📎 Неизвестный")
            if len(media_items) == 1
            else MEDIA_TYPE_NAMES["media_group"]
        )

        info = (
            f"📢 <b>Получена новая предложка</b>\n\n"
            f"🆔 ID: {submission.id}\n"
            f"📅 Дата: {created_at}\n"
            f"📝 Тип: {type_name}\n"
        )

        if user.anonymous_mode:
            info += "\n🎭 Анонимно"
        else:
            info += f"\n👤 <b>Автор:</b>\n"
            info += f"   Имя: {user.full_name or '—'}\n"
            if user.username:
                info += f"   Username: @{user.username}\n"
            info += f"   ID: <code>{user.telegram_id}</code>"

        await bot.send_message(admin.telegram_id, info, parse_mode="HTML")

        # ── content ──────────────────────────────────────────────────────
        if len(media_items) == 1:
            item = media_items[0]
            await send_single_media(
                bot, admin.telegram_id, item.media_type, item.file_id, item.caption
            )
        else:
            await send_media_group_items(bot, admin.telegram_id, media_items)

        # ── action buttons ───────────────────────────────────────────────
        await bot.send_message(
            admin.telegram_id,
            f"Выберите действие для предложки #{submission.id}:",
            reply_markup=admin_submission_keyboard(submission.id),
        )


# ── Cancel ───────────────────────────────────────────────────────────────────


@router.message(UserStates.waiting_for_content, F.text == "❌ Отмена")
async def cancel_submission(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отправка отменена.", reply_markup=main_menu_keyboard())


# ── Receive content ─────────────────────────────────────────────────────────


@router.message(UserStates.waiting_for_content)
async def receive_content(
    message: Message,
    state: FSMContext,
    db: DatabaseEngine,
    bot: Bot,
    album: list[Message] | None = None,
):
    """Handle any supported content type (single or album)."""
    messages = album if album else [message]

    # Validate first item
    first_type, _, _ = detect_media(messages[0])
    if first_type == "unknown":
        await message.answer("❌ Неподдерживаемый тип контента. Попробуйте другой.")
        return

    async with db.session_factory() as session:
        user_service = UserService(session)
        user = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        submission_service = SubmissionService(session)

        # Anti-spam
        if await check_spam(submission_service, user.id):
            await state.clear()
            await message.answer(
                "⚠️ Слишком много предложек! Подождите минуту перед отправкой новых.",
                reply_markup=main_menu_keyboard(),
            )
            return

        # Persist
        submission = await submission_service.create_submission(user.id)

        for msg in messages:
            media_type, file_id, caption = detect_media(msg)
            if media_type != "unknown":
                await submission_service.add_media(
                    submission.id, file_id, media_type, caption
                )

    await state.clear()
    await message.answer(
        "✅ Материал получен и отправлен администрации.",
        reply_markup=main_menu_keyboard(),
    )

    # Notify admin (uses a fresh session inside)
    await notify_admin(bot, db, submission.id)
