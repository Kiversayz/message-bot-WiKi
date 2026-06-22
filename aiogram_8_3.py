from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from idna.uts46data import uts46_starts

from config import *
from game_number import GameNumber


# Вместо BOT TOKEN HERE нужно вставить токен вашего бота, полученный у @BotFather
BOT_TOKEN = TOKEN_ACCESS_API_TG_BOT

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
game_number = GameNumber()


# Хэндлер на команду /start
@dp.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(
        'Привет!\nДавайте сыграем в игру "Угадай число"?\n\n'
        'Чтобы получить правила игры и список доступных '
        'команд - отправьте команду /help'
    )

# Хэндлер на команду /help
@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(
        'Правила игры:\n\nЯ загадываю число от 1 до 100, '
        'а вам нужно его угадать\nУ вас есть 5 '
        'попыток\n\nДоступные команды:\n/help - правила '
        'игры и список команд\n/cancel - выйти из игры\n'
        '/stat - посмотреть статистику\n\nДавай сыграем?'
    )

# Хэндлер на команду /stat
@dp.message(Command(commands='stat'))
async def process_stat_command(message: Message):
    user_id = message.from_user.id

    # Провреряем есть ли данные у пользователя
    if game_number.is_first_game(player_id=user_id):
        await message.answer('Вы еще не играли. Давайте начнем!')
    else:
        # Получаем данные из класса
        player_data = game_number.get_stats(user_id)
        await message.answer(
            f'Всего игр сыграно: {player_data["wins"] + player_data["losses"]}\n'
            f'Игр выиграно: {player_data["wins"]}'
        )

# Хэндлер на команду /cancel
@dp.message(Command(commands='cancel'))
async def process_cancel_command(message: Message):
    user_id = message.from_user.id

    if game_number.check_game_status(user_id):
        game_number.end_game(user_id)
        await message.answer(
            'Вы вышли из игры. Если захотите сыграть '
            'снова - напишите об этом'
        )
    else:
        await message.answer(
            'А мы и так с вами не играем. '
            'Может, сыграем разок?'
        )

# Этот хэндлер будет срабатывать на согласие пользователя сыграть в игру
@dp.message(F.text.lower().in_(['да', 'давай', 'сыграем', 'игра',
                                'играть', 'хочу играть']))
async def process_positive_answer(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not game_number.check_game_status(user_id):
        # Запускаем игру
        game_number.start_new_game(user_id, chat_id)
        await message.answer(
            'Ура!\n\nЯ загадал число от 1 до 100, '
            'попробуй угадать!'
        )
    else:
        await message.answer(
            'Пока мы играем в игру я могу '
            'реагировать только на числа от 1 до 100 '
            'и команды /cancel и /stat'
        )


# Этот хэндлер будет срабатывать на отказ пользователя сыграть в игру
@dp.message(F.text.lower().in_(['нет', 'не', 'не хочу', 'не буду']))
async def process_negative_answer(message: Message):
    user_id = message.from_user.id

    if not game_number.check_game_status(user_id):
        await message.answer(
            'Жаль :(\n\nЕсли захотите поиграть - просто '
            'напишите об этом'
        )
    else:
        await message.answer(
            'Мы же сейчас с вами играем. Присылайте, '
            'пожалуйста, числа от 1 до 100'
        )


# Этот хэндлер будет срабатывать на отправку пользователем чисел от 1 до 100
@dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):
    user_id = message.from_user.id

    if game_number.check_game_status(user_id):
        # Передаем число в ваш класс для обработки
        result = game_number.resume_game(user_id, int(message.text))
        await message.answer(result)
    else:
        await message.answer('Мы еще не играем. Хотите сыграть?')


# Этот хэндлер будет срабатывать на остальные любые сообщения
@dp.message()
async def process_other_answers(message: Message):
    user_id = message.from_user.id

    if game_number.check_game_status(user_id):
        await message.answer(
            'Мы же сейчас с вами играем. '
            'Присылайте, пожалуйста, числа от 1 до 100'
        )
    else:
        await message.answer(
            'Я довольно ограниченный бот, давайте '
            'просто сыграем в игру?'
        )


if __name__ == '__main__':
    dp.run_polling(bot)