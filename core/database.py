from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


# 1. Базовый класс для всех будущих таблиц (моделей)
# Все таблицы, которые мы создадим, будут наследоваться от этого класса.
Base = DeclarativeBase()


# 2. Создаём "движок" (Engine) — это само соединение с базой данных
# Он берёт URL из нашего конфига (core/config.py)
engine = create_async_engine(
    url=settings.database_url,
    echo=settings.DEBUG,  # Если в .env DEBUG=true, будет печатать все SQL-запросы в консоль
)


# 3. Создаём "фабрику сессий"
# Сессия — это инструмент, через который мы будем выполнять запросы (добавлять, читать, удалять)
async_session = async_sessionmaker(
    bind=engine,       # Привязываем к нашему движку
    class_=AsyncSession, # Указываем, что сессия должна быть асинхронной
    expire_on_commit=False, # Полезная настройка: после сохранения данных они остаются доступными
)