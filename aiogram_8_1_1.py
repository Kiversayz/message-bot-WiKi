"""
Регистрация команд или же тригеры для бота на сообщения пользователя.

"""

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from configs.config import *
from game_number import GameNumber


# Вместо BOT TOKEN HERE нужно вставить токен вашего бота, полученный у @BotFather
BOT_TOKEN = TOKEN_ACCESS_API_TG_BOT

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
game_number = GameNumber()


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands="start"))
async def process_start_command(message: Message):
    user_id = message.from_user.id
    if game_number.check_game_status(user_id):
        if game_number.last_send_number(user_id):
            await message.answer(f'Привет!\nВижу ты уже игрешь со мной в игру\nНапоминаю, последний твой ответ был "{game_number.last_send_number(user_id)}"')
        else:
            await message.answer(
                f'Привет!\nВижу ты уже игрешь со мной в игру\nИ я жду от тебя число от 1 до 100')
    await message.answer('Привет!\nМеня зовут Эхо-бот!\nДавай сиграем в игру "Угадай число"')


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer(
        'Напиши мне что-нибудь и в ответ '
        'я пришлю тебе твое сообщение'
    )

"""
# Альтернативный вид записи того же самого что и выше:
# Этот хэндлер будет срабатывать на команду "/start"
async def process_start_command(message: Message):
    await message.answer('Привет!\nМеня зовут Эхо-бот!\nНапиши мне что-нибудь')


# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        'Напиши мне что-нибудь и в ответ '
        'я пришлю тебе твое сообщение'
    )


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
async def send_echo(message: Message):
    await message.reply(text=message.text)
    
# Регистрируем хэндлеры
dp.message.register(process_start_command, Command(commands='start'))
dp.message.register(process_help_command, Command(commands='help'))
dp.message.register(send_echo)
"""

async def process_game_number_command(message: Message):



    await message.answer(
        'Напиши мне что-нибудь и в ответ '
        'я пришлю тебе твое сообщение'
    )


dp.message.register(process_game_number_command, Command(commands='game_number'))


# Этот хэндлер будет срабатывать на любые ваши сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    print(message.model_dump_json(indent=4, exclude_none=True))
    try:
        await message.send_copy(chat_id=message.chat.id)
        await message.answer(message.model_dump_json(indent=4, exclude_none=True))
    except TypeError:
        await message.reply(
            text='Данный тип апдейтов не поддерживается '
                 'методом send_copy'
        )

if __name__ == '__main__':
    dp.run_polling(bot)