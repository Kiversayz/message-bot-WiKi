from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Конфигурация бота.
    """

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота от @BotFather")

    # Confluence
    CONFLUENCE_BASE_URL: str = Field(..., description="URL Confluence (например, https://wiki.company.com)")
    CONFLUENCE_TOKEN: str = Field(..., description="Personal Access Token для Confluence API")

    # Application
    DEBUG: bool = Field(default=False)

    # Pydantic config
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """URL для SQLite. Файл bot.db будет в корне проекта."""
        return "sqlite+aiosqlite:///./bot.db"


# Singleton
settings = Settings()