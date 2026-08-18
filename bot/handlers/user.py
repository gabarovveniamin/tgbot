"""Handlers for regular users: /start, menu navigation, settings."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database import DatabaseEngine
from bot.keyboards import cancel_keyboard, main_menu_keyboard, settings_keyboard
from bot.services import AdminService, UserService
from bot.states import UserStates

router = Router()


# ── /start ───────────────────────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message, db: DatabaseEngine, state: FSMContext):
    await state.clear()

    async with db.session_factory() as session:
        admin_service = AdminService(session)
        user_service = UserService(session)

        # Always save / update user record
        await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        admin = await admin_service.get_admin()

        if not admin:
            # First user ever → becomes the admin
            result = await admin_service.register_admin(message.from_user.id)
            if result:
                await message.answer(
                    "🎉 Вы зарегистрированы как администратор бота!\n"
                    "Вы будете получать все предложки от пользователей.",
                    reply_markup=main_menu_keyboard(),
                )
                return

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Я бот для предложки новостей в канал.\n"
        "Отправьте мне медиа я повторю))",
        reply_markup=main_menu_keyboard(),
    )


# ── Main menu ────────────────────────────────────────────────────────────────


@router.message(F.text == "📰 Отправить новость")
async def send_news(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_content)
    await message.answer(
        "📝 Отправьте мне медиа а я повторю)\n\n"
        "Поддерживаются: текст, фото, видео, GIF, стикеры, "
        "голосовые, видеосообщения, аудио и документы.\n\n"
        "Вы также можете отправить несколько фотографий одновременно (альбом). Буду очень рада любым медиа)",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, state: FSMContext, db: DatabaseEngine):
    await state.clear()

    async with db.session_factory() as session:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        mode = "🎭 Анонимно" if user and user.anonymous_mode else "👤 С подписью"

    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"Текущий режим: <b>{mode}</b>\n\n"
        f"Выберите режим отправки:",
        parse_mode="HTML",
        reply_markup=settings_keyboard(),
    )


@router.message(F.text == "❓ Помощь")
async def help_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Этот бот позволяет предлагать новости для публикации в канале.\n\n"
        "<b>Как отправить новость:</b>\n"
        "1. Нажмите «📰 Отправить новость»\n"
        "2. Отправьте текст, фото, видео, GIF, стикер или другой материал\n"
        "3. Дождитесь ответа от администратора\n\n"
        "<b>Настройки:</b>\n"
        "• 👤 С подписью — ваше имя будет указано при публикации\n"
        "• 🎭 Анонимно — публикация без указания автора\n\n"
        "<b>Поддерживаемые типы:</b>\n"
        "текст, фото, видео, GIF, стикеры, голосовые, "
        "видеосообщения, аудио, документы и альбомы.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ── Settings ─────────────────────────────────────────────────────────────────


@router.message(F.text == "👤 Отправлять с подписью")
async def set_signed(message: Message, db: DatabaseEngine, state: FSMContext):
    await state.clear()
    async with db.session_factory() as session:
        user_service = UserService(session)
        await user_service.set_anonymous_mode(message.from_user.id, False)
    await message.answer(
        "👤 Теперь ваши предложки будут отправляться с подписью.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🎭 Отправлять анонимно")
async def set_anonymous(message: Message, db: DatabaseEngine, state: FSMContext):
    await state.clear()
    async with db.session_factory() as session:
        user_service = UserService(session)
        await user_service.set_anonymous_mode(message.from_user.id, True)
    await message.answer(
        "🎭 Теперь ваши предложки будут отправляться анонимно.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🔙 Назад")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=main_menu_keyboard())
