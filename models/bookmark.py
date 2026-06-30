import datetime
from sqlalchemy import String, BigInteger, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Bookmark(Base):
    __tablename__ = 'bookmarks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    # Возвращаем строку "User", чтобы не было циклического импорта
    user: Mapped['User'] = relationship()
    page_id: Mapped[int] = mapped_column(BigInteger, index=True)
    page_title: Mapped[str] = mapped_column(String(500))
    space_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )