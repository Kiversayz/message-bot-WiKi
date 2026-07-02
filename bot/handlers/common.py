import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from core.config import settings
from services.user_service import get_or_create_user
from services.article_service import get_article, sync_article
from services.bookmark_service import toggle_bookmark, is_bookmarked, get_user_bookmarks
from services.confluence.client import get_confluence_client
from utils.text import split_text_into_pages
from bot.keyboards.inline import get_article_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    user = message.from_user
    db_user = await get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    logger.info(f"Пользователь {db_user.telegram_id} ({db_user.username}) запустил бота")

    await message.answer(
        f"Привет, {user.first_name or 'друг'}! 👋\n\n"
        "Я бот для чтения статьи из корпоративной вики Confluence.\n\n"
        "Команды:\n"
        "/article — прочитать статью\n"
        "/bookmarks — мои закладки\n"
        "/sync — обновить статью из Confluence"
    )


@router.message(Command("sync"))
async def cmd_sync(message: Message):
    """Обработчик команды /sync - синхронизация статьи."""
    await message.answer("⏳ Синхронизирую статью с Confluence...")

    try:
        client = get_confluence_client()
        updated = await sync_article(client)

        if updated:
            await message.answer("✅ Статья успешно обновлена!")
        else:
            await message.answer("ℹ️ Статья уже актуальна.")

    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        await message.answer(f"❌ Ошибка синхронизации: {e}")


@router.message(Command("article"))
async def cmd_article(message: Message):
    """Обработчик команды /article - чтение статьи."""
    db_user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    article = await get_article()

    if not article:
        await message.answer(
            "❌ Статья не найдена.\n\n"
            "Запустите синхронизацию командой /sync"
        )
        return

    pages = split_text_into_pages(article['content'])
    total_pages = len(pages)

    # Проверяем закладку для ПЕРВОЙ страницы
    is_bookmarked_flag = await is_bookmarked(db_user.id, settings.CONFLUENCE_PAGE_ID, page_number=1)

    await message.answer(f"<b>📖 {article['title']}</b>", parse_mode="HTML")

    keyboard = get_article_keyboard(
        current_page=1,
        total_pages=total_pages,
        page_id=settings.CONFLUENCE_PAGE_ID,
        is_bookmarked=is_bookmarked_flag
    )

    await message.answer(
        pages[0],
        parse_mode="HTML",
        reply_markup=keyboard
    )

    logger.info(f"Статья '{article['title']}' отправлена пользователю {message.from_user.id}")


@router.message(Command("bookmarks"))
async def cmd_bookmarks(message: Message):
    """Обработчик команды /bookmarks - список закладок."""
    db_user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    bookmarks = await get_user_bookmarks(db_user.id)

    if not bookmarks:
        await message.answer("📚 У вас пока нет закладок.\n\nДобавьте их при чтении статьи командой /article")
        return

    # Формируем список закладок
    text = "📚 <b>Ваши закладки:</b>\n\n"
    for i, bookmark in enumerate(bookmarks, 1):
        text += f"{i}. <b>{bookmark.page_title}</b>\n"
        text += f"   Страница {bookmark.page_number}\n"
        text += f"   /open_{bookmark.page_id}_{bookmark.page_number}\n\n"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("page:"))
async def callback_page(callback: CallbackQuery):
    """Обработчик переключения страниц."""
    _, page_id_str, page_num_str = callback.data.split(":")
    page_id = int(page_id_str)
    page_num = int(page_num_str)

    article = await get_article()

    if not article:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    pages = split_text_into_pages(article['content'])

    if page_num < 1 or page_num > len(pages):
        await callback.answer("Страница не существует", show_alert=True)
        return

    db_user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )

    # Проверяем закладку для ТЕКУЩЕЙ страницы
    is_bookmarked_flag = await is_bookmarked(db_user.id, page_id, page_number=page_num)

    keyboard = get_article_keyboard(
        current_page=page_num,
        total_pages=len(pages),
        page_id=page_id,
        is_bookmarked=is_bookmarked_flag
    )

    await callback.message.edit_text(
        pages[page_num - 1],
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data.startswith("bookmark:"))
async def callback_bookmark(callback: CallbackQuery):
    """Обработчик добавления/удаления закладки."""
    _, page_id_str, page_num_str = callback.data.split(":")
    page_id = int(page_id_str)
    page_num = int(page_num_str)

    article = await get_article()

    if not article:
        await callback.answer("Статья не найдена", show_alert=True)
        return

    db_user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )

    try:
        is_now_bookmarked = await toggle_bookmark(
            user_id=db_user.id,
            page_id=page_id,
            page_title=article['title'],
            space_key="UNKNOWN",
            page_number=page_num  # Передаём номер страницы
        )

        # Определяем общее количество страниц
        total_pages = len(split_text_into_pages(article['content']))

        # Обновляем клавиатуру
        keyboard = get_article_keyboard(
            current_page=page_num,
            total_pages=total_pages,
            page_id=page_id,
            is_bookmarked=is_now_bookmarked
        )

        await callback.message.edit_reply_markup(reply_markup=keyboard)

        if is_now_bookmarked:
            await callback.answer(f"⭐ Страница {page_num} добавлена в закладки", show_alert=False)
        else:
            await callback.answer(f"Страница {page_num} удалена из закладок", show_alert=False)

    except Exception as e:
        logger.error(f"Ошибка работы с закладкой: {e}")
        await callback.answer("Ошибка при работе с закладкой", show_alert=True)


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Обработчик неактивной кнопки (индикатор страницы)."""
    await callback.answer()


@router.message(F.text.startswith("/open_"))
async def cmd_open_bookmark(message: Message):
    """Обработчик открытия конкретной закладки."""
    # Парсим команду: /open_216643310_3
    try:
        parts = message.text.split("_")
        page_id = int(parts[1])
        page_num = int(parts[2])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды")
        return

    article = await get_article()

    if not article:
        await message.answer("❌ Статья не найдена")
        return

    pages = split_text_into_pages(article['content'])

    if page_num < 1 or page_num > len(pages):
        await message.answer("❌ Страница не существует")
        return

    db_user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    is_bookmarked_flag = await is_bookmarked(db_user.id, page_id, page_number=page_num)

    await message.answer(f"<b>📖 {article['title']}</b> (закладка)", parse_mode="HTML")

    keyboard = get_article_keyboard(
        current_page=page_num,
        total_pages=len(pages),
        page_id=page_id,
        is_bookmarked=is_bookmarked_flag
    )

    await message.answer(
        pages[page_num - 1],
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(F.text)
async def echo(message: Message):
    """Эхо ответ сообщением пользователя на текст текстом"""
    text = message.text

    logger.info(f"Пользователь написал '{text}'")

    await message.answer(
        f'Ты написал , "{text}" 👋\n\n'
        '/start — получить список команд'
    )
