import logging
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


class ConfluenceParser:
    """
    Парсер для конвертации XHTML-формата Confluence (body.storage)
    в HTML-формат, совместимый с Telegram.

    Причина существования:
    Confluence хранит контент в собственном формате (storage format)
    с макросами (<ac:structured-macro>) и inline-стилями (<span style="...">).
    Telegram не понимает эти теги и поддерживает только ограниченный набор HTML.

    Пайплайн обработки:
    1. Парсинг сырого XHTML в дерево DOM (BeautifulSoup).
    2. Замена специфичных макросов Confluence на стандартные HTML-теги.
    3. Очистка от inline-стилей (удаление <span>).
    4. Конвертация очищенного HTML в Markdown (промежуточный формат).
    5. Преобразование Markdown в Telegram HTML.
    6. Экранирование спецсимволов для безопасного парсинга Telegram.
    """

    def parse(self, xhtml_content: str) -> str:
        """
        Главный метод, запускающий полный цикл конвертации.

        :param xhtml_content: Сырая строка XHTML из поля body.storage.value API Confluence.
        :return: Готовая строка, которую можно передать в Telegram Bot API
                 с parse_mode='HTML'.
        """
        if not xhtml_content:
            logger.warning("Получен пустой контент для парсинга.")
            return ""

        logger.debug(f"Начало парсинга. Длина входного XHTML: {len(xhtml_content)} символов.")

        # Шаг 1: Создание дерева DOM для удобной навигации и изменения элементов
        soup = BeautifulSoup(xhtml_content, 'html.parser')

        # Шаг 2 и 3: Очистка и нормализация структуры
        soup = self._process_macros(soup)
        soup = self._clean_inline_styles(soup)

        # Шаг 4: Конвертация в Markdown для упрощения дальнейшей работы с тегами
        # strip=['span', 'div'] удаляет эти теги, оставляя только их текстовое содержимое
        markdown_text = md(str(soup), strip=['span', 'div'])

        # Шаг 5 и 6: Форматирование под Telegram и экранирование
        telegram_html = self._markdown_to_telegram_html(markdown_text)
        telegram_html = self._escape_telegram_chars(telegram_html)

        logger.debug(f"Парсинг завершен. Длина итогового HTML: {len(telegram_html)} символов.")
        return telegram_html.strip()

    def _process_macros(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Заменяет кастомные макросы Confluence на стандартные HTML-теги.

        Причина: Telegram не знает, что такое <ac:structured-macro>.
        Нам нужно превратить их в понятные <pre>, <code> или текст.

        :param soup: Объект BeautifulSoup с XHTML-контентом.
        :return: Модифицированный объект BeautifulSoup.
        """
        # Обработка макросов кода (Code Block)
        for macro in soup.find_all('ac:structured-macro', {'ac:name': 'code'}):
            code_body = macro.find('ac:plain-text-body')
            if code_body and code_body.string:
                # Создаем стандартные теги <pre><code>...</code></pre>
                pre_tag = soup.new_tag('pre')
                code_tag = soup.new_tag('code')
                code_tag.string = code_body.string
                pre_tag.append(code_tag)
                macro.replace_with(pre_tag)
                logger.debug("Найден и обработан макрос кода.")

        # Обработка макросов изображений (Image)
        for image in soup.find_all('ac:image'):
            attachment = image.find('ri:attachment')
            filename = attachment.get('ri:filename') if attachment else 'image'
            # В Telegram картинки отправляются отдельным методом send_photo.
            # Здесь мы просто оставляем текстовую пометку, чтобы не терять контекст.
            placeholder = soup.new_string(f"\n[ Изображение: {filename}]\n")
            image.replace_with(placeholder)
            logger.debug(f"Найден и обработан макрос изображения: {filename}.")

        return soup

    def _clean_inline_styles(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Удаляет теги <span> с inline-стилями, оставляя только текст.

        Причина: Confluence часто оборачивает обычный текст в
        <span style="color: rgb(68,68,68);">. Telegram не поддерживает
        атрибут style, поэтому теги нужно "развернуть" (unwrap).

        :param soup: Объект BeautifulSoup.
        :return: Модифицированный объект BeautifulSoup.
        """
        for span in soup.find_all('span', style=True):
            span.unwrap()
        return soup

    def _markdown_to_telegram_html(self, markdown_text: str) -> str:
        """
        Преобразует базовый Markdown в HTML-теги, поддерживаемые Telegram.

        Причина: Telegram HTML поддерживает только <b>, <i>, <u>, <s>, <code>,
        <pre>, <a>. Регулярные выражения заменяют синтаксис Markdown на эти теги.

        :param markdown_text: Строка в формате Markdown.
        :return: Строка с HTML-тегами Telegram.
        """
        html = markdown_text

        # Заголовки Markdown (# Текст) -> Жирный текст (<b>Текст</b>)
        # Telegram не поддерживает теги <h1>-<h6>, поэтому используем <b>
        html = re.sub(r'^### (.+)$', r'<b>\1</b>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<b>\1</b>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<b>\1</b>', html, flags=re.MULTILINE)

        # Жирный текст (**текст**) -> <b>текст</b>
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)

        # Курсив (*текст*) -> <i>текст</i>
        # Используем негативный lookbehind/lookahead, чтобы не задеть жирный текст
        html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html)

        # Инлайн-код (`код`) -> <code>код</code>
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        return html

    def _escape_telegram_chars(self, text: str) -> str:
        """
        Экранирует символы, которые Telegram воспринимает как служебные.

        Причина: Если в тексте статьи встретятся символы '<', '>' или '&',
        Telegram может попытаться распарсить их как HTML-теги и выдать ошибку
        "Bad Request: can't parse entities". Их нужно заменить на HTML-сущности.

        ВАЖНО: Экранирование делается ПОСЛЕ расстановки наших тегов <b>, <i> и т.д.,
        иначе мы экранируем сами теги.

        :param text: Строка с уже расставленными HTML-тегами Telegram.
        :return: Безопасная строка для отправки в Telegram.
        """
        # Сначала экранируем амперсанд, чтобы не задеть уже добавленные сущности
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return text