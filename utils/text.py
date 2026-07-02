import re


def split_text_into_pages(text: str, max_length: int = 600) -> list[str]:
    """
    Разбивает длинный текст на страницы для Telegram.

    Args:
        text: Исходный текст
        max_length: Максимальная длина одной страницы (символы)

    Returns:
        Список строк-страниц
    """
    if len(text) <= max_length:
        return [text]

    pages = []
    current_page = ""

    # Разбиваем текст на абзацы по двойным переносам строк
    paragraphs = re.split(r'\n\n+', text)

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Проверяем, поместится ли абзац на текущую страницу
        if len(current_page) + len(paragraph) + 2 <= max_length:
            # Поместится - добавляем
            if current_page:
                current_page += "\n\n" + paragraph
            else:
                current_page = paragraph
        else:
            # Не поместится - сохраняем текущую страницу и начинаем новую
            if current_page:
                pages.append(current_page)

            # Если сам абзац длиннее max_length - разбиваем его по предложениям
            if len(paragraph) > max_length:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_page = ""

                for sentence in sentences:
                    if len(current_page) + len(sentence) + 1 <= max_length:
                        if current_page:
                            current_page += " " + sentence
                        else:
                            current_page = sentence
                    else:
                        if current_page:
                            pages.append(current_page)
                        current_page = sentence
            else:
                current_page = paragraph

    # Добавляем последнюю страницу
    if current_page:
        pages.append(current_page)

    return pages if pages else [""]