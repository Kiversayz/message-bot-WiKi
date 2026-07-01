from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session
from models import User


async def get_or_create_user(
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
) -> User:
    """
    Возвращает существующего пользователя по telegram_id
    или создаёт нового, если такого нет в БД.
    """
    async with async_session() as session:
        # Ищем пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # [Логика] Создаём нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)  # Обновляем объект, чтобы получить id

        return user