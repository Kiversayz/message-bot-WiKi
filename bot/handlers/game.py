import logging
import re
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import GameState
from utils.game_number import get_game_instance

router = Router()
logger = logging.getLogger(__name__)


@router.message(
    ~StateFilter(GameState.playing),  # Состояние НЕ "playing"
    F.text.regexp(r'^(да|давай|играть|хочу играть)$', flags=re.IGNORECASE)
)
async def cmd_start_game(message: Message, state: FSMContext):
    """Запуск игры при вводе ключевых слов."""
    game = get_game_instance()
    player_id = message.from_user.id

    # Запускаем новую игру
    secret_number = game.start_new_game(player_id, message.chat.id)

    # Переключаем пользователя в состояние "playing"
    await state.set_state(GameState.playing)

    logger.info(f"Пользователь {player_id} начал игру. Загадано: {secret_number}")

    await message.answer(
        "🎮 <b>Игра началась!</b>\n\n"
        "Я загадал число от 1 до 100. Попробуй угадать!\n"
        "Просто напиши число в чат.\n\n"
        "Если захочешь выйти — напиши <b>Стоп</b>, <b>Нет</b> или <b>Хватит</b>.",
        parse_mode="HTML"
    )


@router.message(
    StateFilter(GameState.playing),  # Только в состоянии "playing"
    F.text.regexp(r'^(нет|стоп|хватит|не)$', flags=re.IGNORECASE)
)
async def cmd_stop_game(message: Message, state: FSMContext):
    """Остановка игры по ключевым словам."""
    game = get_game_instance()
    player_id = message.from_user.id

    # Завершаем игру
    game.end_game(player_id)

    # Сбрасываем состояние
    await state.clear()

    logger.info(f"Пользователь {player_id} остановил игру")

    await message.answer(
        "🛑 Игра остановлена.\n\n"
        "Возвращаемся в обычный режим. Можешь продолжить читать статью (/article) "
        "или начать новую игру командой 'Да'."
    )


@router.message(StateFilter(GameState.playing))
async def process_game_guess(message: Message, state: FSMContext):
    """Обработка попытки угадать число."""
    game = get_game_instance()
    player_id = message.from_user.id
    text = message.text.strip()

    # 1. Пытаемся преобразовать в число
    try:
        number = int(text)
    except ValueError:
        await message.answer(
            "🤔 Это не число.\n\n"
            "Сейчас бот принимает только числа в диапазоне от 1 до 100.\n"
            "Если хочешь прекратить игру — напиши <b>Стоп</b>.",
            parse_mode="HTML"
        )
        return

    # 2. Проверяем диапазон
    if number < 1 or number > 100:
        await message.answer(
            f"🔢 Число {number} вне диапазона.\n\n"
            "Сейчас бот принимает только числа в диапазоне от 1 до 100.\n"
            "Если хочешь прекратить игру — напиши <b>Стоп</b>.",
            parse_mode="HTML"
        )
        return

    # 3. Передаём в модуль игры и получаем результат
    result_text = game.resume_game(player_id, number)

    # 4. Проверяем, закончилась ли игра
    game_status = game.check_game_status(player_id)

    if not game_status:
        # Игра окончена (победа или поражение)
        await state.clear()
        await message.answer(
            result_text + "\n\nМожешь начать новую игру командой 'Да'.",
            parse_mode="HTML"
        )
        logger.info(f"Игра пользователя {player_id} завершена")
    else:
        # Игра продолжается
        stats = game.get_stats(player_id)
        tries_left = game.lose_tries - stats['tries']

        await message.answer(
            f"{result_text}\n\n"
            f"Попыток осталось: {tries_left}",
            parse_mode="HTML"
        )