import logging
import httpx
from typing import Optional, Dict, Any
from core.config import settings


logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def close(self):
        """Корректное закрытие клиента при остановке бота"""
        await self.client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Универсальный метод для запросов"""
        url = f"{self.base_url}/rest/api/{endpoint}"

        try:
            response = await self.client.request(method, url, **kwargs)

            # raise_for_status() выбросит исключение, если код ответа 4xx или 5xx
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            # Ошибки от самого Confluence (401, 403, 404, 500)
            logger.error(f"HTTP ошибка {e.response.status_code} на {url}: {e.response.text}")
        except httpx.RequestError as e:
            # Сетевые ошибки (таймаут, DNS, нет интернета)
            logger.error(f"Сетевая ошибка при запросе к {url}: {e}")
        except Exception as e:
            # Любые другие непредвиденные ошибки (например, JSON не распарсился)
            logger.exception(f"Непредвиденная ошибка на {url}: {e}")

        return None


    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Проверка токена при старте"""
        return await self._request("GET", "user/current")

    async def get_spaces(self, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Главное меню (Разделы)"""
        return await self._request("GET", "space", params={"limit": limit})

    async def get_content(self, space_key: Optional[str] = None, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Список страниц (Главы)"""
        params = {"limit": limit}
        if space_key:
            params["spaceKey"] = space_key
        return await self._request("GET", "content", params=params)

    async def get_page_by_id(self, page_id: str, expand: str = "body.storage") -> Optional[Dict[str, Any]]:
        """Текст страницы (Чтение)"""
        return await self._request("GET", f"content/{page_id}", params={"expand": expand})

    async def search(self, cql: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Поиск по ключевым словам"""
        return await self._request("GET", "content/search", params={"cql": cql, "limit": limit})


# Синглтон: один клиент на всё приложение
_client_instance: ConfluenceClient | None = None


def get_confluence_client() -> ConfluenceClient:
    """
    Возвращает единственный экземпляр ConfluenceClient.
    При первом вызове создаёт его, при последующих — возвращает тот же.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ConfluenceClient(
            base_url=settings.CONFLUENCE_BASE_URL,
            token=settings.CONFLUENCE_TOKEN
        )
    return _client_instance