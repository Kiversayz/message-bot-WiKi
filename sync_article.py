import asyncio
import logging

from services.confluence.client import get_confluence_client
from services.article_service import sync_article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Запуск синхронизации статьи...")

    # ← Получаем клиент через синглтон
    client = get_confluence_client()

    try:
        updated = await sync_article(client)

        if updated:
            logger.info("✅ Статья успешно синхронизирована")
        else:
            logger.info("ℹ️ Статья уже актуальна, обновление не требуется")

    finally:
        await client.close()
        logger.info("Синхронизация завершена")


if __name__ == "__main__":
    asyncio.run(main())