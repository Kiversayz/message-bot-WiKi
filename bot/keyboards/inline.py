from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_article_keyboard(
        current_page: int,
        total_pages: int,
        page_id: int,
        is_bookmarked: bool = False
) -> InlineKeyboardMarkup:
    """
    Создаёт инлайн-клавиатуру для навигации по статье.
    """
    buttons = []

    if total_pages > 1:
        nav_buttons = []

        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"page:{page_id}:{current_page - 1}"
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="noop"
            )
        )

        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперёд ▶️",
                    callback_data=f"page:{page_id}:{current_page + 1}"
                )
            )

        buttons.append(nav_buttons)

    # Добавляем page_num в callback_data для закладки
    bookmark_text = "⭐ Убрать из закладок" if is_bookmarked else "⭐ В закладки"
    buttons.append([
        InlineKeyboardButton(
            text=bookmark_text,
            callback_data=f"bookmark:{page_id}:{current_page}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)