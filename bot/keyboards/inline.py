from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_submission_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    """Inline buttons shown to admin under each submission."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data=f"publish:{submission_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject:{submission_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Ответить",
                    callback_data=f"reply:{submission_id}",
                ),
            ],
        ]
    )
