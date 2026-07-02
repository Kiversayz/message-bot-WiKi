from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
        # Пытаемся создать сразу (оптимистичный подход)
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)

        try:
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            # Если пользователь уже существует - откатываем и ищем
            await session.rollback()
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one()