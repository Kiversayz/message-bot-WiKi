from sqlalchemy import String, BigInteger, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base
import datetime


class PageCache(Base):
    __tablename__ = "page_cache"

    page_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    space_key: Mapped[str] = mapped_column(String(100),index=True)
    version: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(32),nullable=True)
    last_fetched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))