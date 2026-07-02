import logging
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from core.database import async_session
from models import Bookmark

logger = logging.getLogger(__name__)


async def toggle_bookmark(
        user_id: int,
        page_id: int,
        page_title: str,
        space_key: str,
        page_number: int = 1
) -> bool:
    """
    Добавляет или удаляет закладку (toggle).

    Args:
        user_id: ID пользователя в БД
        page_id: ID страницы Confluence
        page_title: Заголовок страницы
        space_key: Ключ пространства
        page_number: Номер страницы пагинации

    Returns:
        True если закладка добавлена, False если удалена
    """
    try:
        async with async_session() as session:
            # Проверяем, есть ли уже закладка на ЭТУ страницу
            result = await session.execute(
                select(Bookmark).where(
                    Bookmark.user_id == user_id,
                    Bookmark.page_id == page_id,
                    Bookmark.page_number == page_number
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Закладка есть - удаляем
                await session.delete(existing)
                await session.commit()
                logger.info(f"Закладка удалена: user={user_id}, page={page_id}, page_number={page_number}")
                return False
            else:
                # Закладки нет - добавляем
                bookmark = Bookmark(
                    user_id=user_id,
                    page_id=page_id,
                    page_title=page_title,
                    space_key=space_key,
                    page_number=page_number
                )
                session.add(bookmark)
                await session.commit()
                logger.info(f"Закладка добавлена: user={user_id}, page={page_id}, page_number={page_number}")
                return True

    except IntegrityError as e:
        logger.error(f"Нарушение уникальности при работе с закладкой: {e}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при работе с закладкой: {e}")
        raise


async def is_bookmarked(user_id: int, page_id: int, page_number: int = 1) -> bool:
    """Проверяет, добавлена ли конкретная страница в закладки."""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Bookmark).where(
                    Bookmark.user_id == user_id,
                    Bookmark.page_id == page_id,
                    Bookmark.page_number == page_number
                )
            )
            return result.scalar_one_or_none() is not None
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при проверке закладки: {e}")
        return False


async def get_user_bookmarks(user_id: int) -> list[Bookmark]:
    """Возвращает все закладки пользователя."""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Bookmark)
                .where(Bookmark.user_id == user_id)
                .order_by(Bookmark.created_at.desc())
            )
            return list(result.scalars().all())
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при получении закладок: {e}")
        return []