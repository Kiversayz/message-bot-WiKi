import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from core.database import engine, Base
from services.confluence.client import ConfluenceClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Запуск бота...")

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    confluence_client = ConfluenceClient(
        base_url=settings.CONFLUENCE_BASE_URL,
        token=settings.CONFLUENCE_TOKEN,
    )
    dp["confluence_client"] = confluence_client

    # Создание таблиц в БД при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        logger.info("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка бота...")
        await confluence_client.close()
        await engine.dispose()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")