import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from core.database import async_session
from models import PageCache
from services.confluence.client import ConfluenceClient
from services.confluence.parser import ConfluenceParser
from core.config import settings

logger = logging.getLogger(__name__)


async def sync_article(confluence_client: ConfluenceClient) -> bool:
    """
    Синхронизирует статью из Confluence в базу данных.

    Логика работы:
    1. Запрашивает текущую версию статьи из Confluence API
    2. Проверяет, есть ли статья в БД и какая у неё версия
    3. Если версии совпадают - ничего не делает (статья актуальна)
    4. Если версии разные - загружает контент, парсит и сохраняет в БД

    Args:
        confluence_client: Экземпляр клиента Confluence

    Returns:
        True если статья была обновлена, False если уже актуальна
    """
    page_id = settings.CONFLUENCE_PAGE_ID

    try:
        # 1. Запрашиваем метаданные страницы (без контента, чтобы проверить версию)
        logger.info(f"Проверка версии статьи {page_id} в Confluence...")
        page_meta = await confluence_client.get_page_by_id(
            page_id=str(page_id),
            expand="version"  # Запрашиваем только версию, без body
        )

        if not page_meta:
            logger.error(f"Не удалось получить метаданные страницы {page_id}")
            return False

        confluence_version = page_meta["version"]["number"]
        confluence_title = page_meta.get("title", "Без названия")

        logger.info(f"Версия в Confluence: {confluence_version}, заголовок: {confluence_title}")

        # 2. Проверяем версию в БД
        async with async_session() as session:
            result = await session.execute(
                select(PageCache).where(PageCache.page_id == page_id)
            )
            cached_page = result.scalar_one_or_none()

            # 3. Сравниваем версии
            if cached_page and cached_page.version == confluence_version:
                logger.info(f"Статья {page_id} уже актуальна (версия {confluence_version})")
                return False

            # 4. Версии разные - загружаем полный контент
            logger.info(f"Обнаружена новая версия. Загрузка контента...")
            page_full = await confluence_client.get_page_by_id(
                page_id=str(page_id),
                expand="body.storage,version"
            )

            if not page_full:
                logger.error(f"Не удалось получить контент страницы {page_id}")
                return False

            # 5. Парсим XHTML в Telegram HTML
            raw_xhtml = page_full["body"]["storage"]["value"]
            parser = ConfluenceParser()
            parsed_content = parser.parse(raw_xhtml)

            # 6. Сохраняем или обновляем запись в БД
            if cached_page:
                # Обновляем существующую запись
                cached_page.title = confluence_title
                cached_page.version = confluence_version
                cached_page.parsed_content = parsed_content
                cached_page.last_fetched_at = datetime.utcnow()
                logger.info(f"Обновлена существующая запись в БД")
            else:
                # Создаём новую запись
                new_page = PageCache(
                    page_id=page_id,
                    title=confluence_title,
                    space_key=page_full.get("space", {}).get("key", "UNKNOWN"),
                    version=confluence_version,
                    parsed_content=parsed_content,
                    last_fetched_at=datetime.utcnow()
                )
                session.add(new_page)
                logger.info(f"Создана новая запись в БД")

            await session.commit()
            logger.info(f"Статья {page_id} успешно синхронизирована (версия {confluence_version})")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при синхронизации: {e}")
        return False
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при синхронизации: {e}")
        return False


async def get_article() -> dict | None:
    """
    Получает статью из базы данных для отображения.

    Returns:
        Словарь с полями 'title' и 'content' или None если статья не найдена
    """
    page_id = settings.CONFLUENCE_PAGE_ID

    try:
        async with async_session() as session:
            result = await session.execute(
                select(PageCache).where(PageCache.page_id == page_id)
            )
            cached_page = result.scalar_one_or_none()

            if not cached_page:
                logger.warning(f"Статья {page_id} не найдена в БД. Запустите синхронизацию.")
                return None

            return {
                "title": cached_page.title,
                "content": cached_page.parsed_content
            }

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при получении статьи: {e}")
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении статьи: {e}")
        return None