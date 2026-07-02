import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from core.database import engine, Base
from bot.handlers.common import router as common_router
from services.confluence.client import get_confluence_client

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

    dp.include_router(common_router)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        logger.info("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка бота...")
        # ← Закрываем клиент-синглтон
        client = get_confluence_client()
        await client.close()
        await engine.dispose()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")