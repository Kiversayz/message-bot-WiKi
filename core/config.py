from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Централизованное хранилище конфигурации приложения.

    Загружает переменные из .env файла и валидирует их типы.
    При отсутствии обязательных полей выбросит ошибку при старте.
    """

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота от @BotFather")
    BOT_USERNAME: str = Field(default="", description="Username бота без @")

    # Confluence
    CONFLUENCE_BASE_URL: str = Field(..., description="Базовый URL Confluence (например, https://wiki.company.com)")
    CONFLUENCE_TOKEN: str = Field(..., description="Personal Access Token для Confluence API")

    # PostgreSQL
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="confluence_bot")
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)

    # Redis
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    # Application
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # Pydantic config
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # Путь к .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Игнорировать неизвестные переменные в .env
    )

    @property
    def database_url(self) -> str:
        """Формирует строку подключения к PostgreSQL (asyncpg)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Формирует строку подключения к Redis."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def confluence_api_url(self) -> str:
        """Формирует базовый URL для REST API Confluence."""
        return f"{self.CONFLUENCE_BASE_URL.rstrip('/')}/rest/api"


# Singleton — один экземпляр на всё приложение
settings = Settings()