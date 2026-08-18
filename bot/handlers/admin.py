"""Admin-only handlers: publish / reject / reply via inline buttons + FSM."""

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Config
from bot.database import DatabaseEngine
from bot.handlers.submissions import send_media_group_items, send_single_media
from bot.keyboards import main_menu_keyboard
from bot.services import AdminService, SubmissionService, UserService
from bot.states import AdminStates

router = Router()


# ── Publish ──────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("publish:"))
async def publish_submission(
    callback: CallbackQuery, db: DatabaseEngine, bot: Bot
):
    submission_id = int(callback.data.split(":")[1])
    config = Config.load()

    async with db.session_factory() as session:
        admin_service = AdminService(session)
        if not await admin_service.is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
            return

        submission_service = SubmissionService(session)
        submission = await submission_service.get_submission(submission_id)

        if not submission or submission.status != "pending":
            await callback.answer(
                "⚠️ Предложка не найдена или уже обработана.", show_alert=True
            )
            return

        user_service = UserService(session)
        user = await user_service.get_user_by_id(submission.user_id)

        media_items = submission.media_items
        if not media_items:
            await callback.answer("❌ Нет контента для публикации.", show_alert=True)
            return

        # Build optional author signature
        author_text = ""
        if user and not user.anonymous_mode:
            author_text = f"\n\n✍️ {user.full_name or ''}"
            if user.username:
                author_text += f" (@{user.username})"

        # Publish to channel
        if len(media_items) == 1:
            item = media_items[0]
            cap = item.caption
            if author_text:
                cap = (cap or "") + author_text
            await send_single_media(
                bot, config.channel_id, item.media_type, item.file_id, cap
            )
        else:
            await send_media_group_items(
                bot, config.channel_id, media_items, author_text
            )

        await submission_service.update_status(submission_id, "published")

        # Notify the author
        if user:
            try:
                await bot.send_message(
                    user.telegram_id,
                    "🎉 Ваша предложка была опубликована в канале!",
                )
            except Exception:
                pass

    await callback.answer("✅ Опубликовано!")
    try:
        await callback.message.edit_text(
            f"✅ Предложка #{submission_id} — опубликована."
        )
    except Exception:
        pass


# ── Reject ───────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("reject:"))
async def reject_submission(
    callback: CallbackQuery, db: DatabaseEngine, bot: Bot
):
    submission_id = int(callback.data.split(":")[1])

    async with db.session_factory() as session:
        admin_service = AdminService(session)
        if not await admin_service.is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
            return

        submission_service = SubmissionService(session)
        submission = await submission_service.get_submission(submission_id)

        if not submission or submission.status != "pending":
            await callback.answer(
                "⚠️ Предложка не найдена или уже обработана.", show_alert=True
            )
            return

        user_service = UserService(session)
        user = await user_service.get_user_by_id(submission.user_id)

        await submission_service.update_status(submission_id, "rejected")

        if user:
            try:
                await bot.send_message(
                    user.telegram_id, "❌ Ваша предложка была отклонена."
                )
            except Exception:
                pass

    await callback.answer("❌ Отклонено!")
    try:
        await callback.message.edit_text(
            f"❌ Предложка #{submission_id} — отклонена."
        )
    except Exception:
        pass


# ── Reply (step 1: ask admin for text) ───────────────────────────────────────


@router.callback_query(F.data.startswith("reply:"))
async def reply_to_submission(
    callback: CallbackQuery, state: FSMContext, db: DatabaseEngine
):
    submission_id = int(callback.data.split(":")[1])

    async with db.session_factory() as session:
        admin_service = AdminService(session)
        if not await admin_service.is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
            return

        submission_service = SubmissionService(session)
        submission = await submission_service.get_submission(submission_id)
        if not submission:
            await callback.answer("❌ Предложка не найдена.", show_alert=True)
            return

    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(submission_id=submission_id)
    await callback.answer()
    await callback.message.answer(
        f"💬 Введите ответ для автора предложки #{submission_id}:\n"
        f"Отправьте /cancel для отмены."
    )


# ── Reply (step 2a: cancel) ─────────────────────────────────────────────────


@router.message(AdminStates.waiting_for_reply, F.text == "/cancel")
async def cancel_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Ответ отменён.", reply_markup=main_menu_keyboard())


# ── Reply (step 2b: send reply to user) ─────────────────────────────────────


@router.message(AdminStates.waiting_for_reply)
async def process_reply(
    message: Message, state: FSMContext, db: DatabaseEngine, bot: Bot
):
    data = await state.get_data()
    submission_id = data.get("submission_id")

    if not submission_id:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуйте ещё раз.")
        return

    async with db.session_factory() as session:
        submission_service = SubmissionService(session)
        submission = await submission_service.get_submission(submission_id)
        if not submission:
            await state.clear()
            await message.answer("❌ Предложка не найдена.")
            return

        user_service = UserService(session)
        user = await user_service.get_user_by_id(submission.user_id)
        if not user:
            await state.clear()
            await message.answer("❌ Пользователь не найден.")
            return

        try:
            await bot.send_message(
                user.telegram_id,
                f"💬 <b>Ответ от администратора</b> "
                f"(предложка #{submission_id}):\n\n{message.text}",
                parse_mode="HTML",
            )
            await message.answer(
                "✅ Ответ отправлен пользователю.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            await message.answer(
                f"❌ Не удалось отправить ответ: {e}",
                reply_markup=main_menu_keyboard(),
            )

    await state.clear()
