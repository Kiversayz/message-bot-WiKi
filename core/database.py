from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


# Правильный способ создания Base в SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass


# Движок для SQLite
engine = create_async_engine(
    url=settings.database_url,
    echo=settings.DEBUG,
)

# Фабрика сессий
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)