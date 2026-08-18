from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main bot menu with three options."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📰 Отправить новость")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


def settings_keyboard() -> ReplyKeyboardMarkup:
    """Settings menu: choose signed or anonymous mode."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Отправлять с подписью")],
            [KeyboardButton(text="🎭 Отправлять анонимно")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Single cancel button shown during content submission."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )
