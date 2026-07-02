from aiogram.fsm.state import StatesGroup, State


class GameState(StatesGroup):
    """Состояния для игры 'Угадай число'."""
    playing = State()  # Пользователь в процессе игры