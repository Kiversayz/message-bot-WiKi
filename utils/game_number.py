import random


class GameNumber:
    def __init__ (self) -> None:
        self._game_data = {}
        self.lose_tries=5


    def is_first_game(self, player_id: int) -> bool:
        """ Проверка, играл ли данный игрок ранее"""
        if player_id not in self._game_data:
            return True
        return False

    def start_new_game(self, player_id: int, chat_id: int)-> int:
        """Начала игры, базавая установка для того кто не играл ранее
        и для того кто уже играл ранее"""
        if self.is_first_game(player_id):
            self._game_data[player_id] = {
                'number': random.randint(1, 100),
                'chat_id': chat_id,
                'wins': 0,
                'losses': 0,
                'tries': 0,
                'game_status': True,
                'last_send_number': None
            }
        else:
            self._game_data[player_id]['tries'] = 0
            self._game_data[player_id]['game_status'] = True
            self._game_data[player_id]['number'] = random.randint(1, 100)

        return self._game_data[player_id]['number']

    def get_stats(self, player_id: int) -> dict:
        return self._game_data[player_id]

    def check_game_status(self,player_id: int) -> bool:
        """Проверка статуса игры"""
        if self.is_first_game(player_id):
            return False
        else:
            return self._game_data[player_id]['game_status']

    def _check_send_number(self,player_id: int, number: int) -> bool:
        """Сранвнение введеного числа с загаданным"""
        self._game_data[player_id]['last_send_number'] = number
        return self._game_data[player_id]['number'] == number

    def _check_send_number_more (self, player_id: int, number: int) -> bool:
        """Проверка введенного числа, больше ли загаданного?"""
        return self._game_data[player_id]['number'] < number

    def _check_lose(self,player_id: int) -> bool:
        """Проверка - проиграл ли игрок?"""
        return  self._game_data[player_id]['tries'] == self.lose_tries

    def _add_tries (self,player_id: int) -> None:
        """Добавлаем +1 к счетчику попыток"""
        self._game_data[player_id]['tries'] += 1

    def end_game (self,player_id: int) -> None:
        """Конец игры"""
        self._game_data[player_id]['tries'] = 0
        self._game_data[player_id]['game_status'] = False
        self._game_data[player_id]['last_send_number'] = None

    def _end_game_lose(self,player_id: int) -> None:
        """Проигрышь"""
        self.end_game(player_id)
        self._game_data[player_id]['losses'] += 1

    def _end_game_win(self,player_id: int) -> None:
        """Выигрышь"""
        self.end_game(player_id)
        self._game_data[player_id]['wins'] += 1

    def last_send_number(self,player_id: int) -> int:
        """Последний введеный номер - пользователем"""
        return self._game_data[player_id]['last_send_number']

    def resume_game (self,player_id: int, send_number: int) -> str | None:
        """Продолжение игры после старта - уведомлениея о состоянии игры"""
        if not isinstance(send_number,int):
            return 'Данное знаение не является числом, пожалуйста введите число от 1 до 100. \nЕсли хотите закончить игру, введите "/close".'
        elif send_number > 100 or send_number < 1:
            return 'Данное знаение не является допустимым по значению, пожалуйста введите число от 1 до 100. \nЕсли хотите закончить игру, введите "/close".'

        check_send_number = self._check_send_number(player_id, send_number)

        if check_send_number:
            self._end_game_win(player_id)
            return f'Ура, ты смог угадать, загаданное число и в правду {send_number}. Если ты хочешь повторить просто напиши /start.'
        else:
            self._add_tries(player_id)
            if self._check_lose(player_id):
                text_end = self._game_data[player_id]['number']
                self._end_game_lose(player_id)
                return f'К сожалению ты проиграл, загаданное число было {text_end}. Игра окончена. Для начала новой игры напиши /start.'
            else:
                text_end = ''
                if self._check_send_number_more(player_id, send_number):
                    text_end += 'Меньше!'
                else:
                    text_end += 'Больше!'
                return f'Не угадал! {text_end}'


# Синглтон: один экземпляр игры на всё приложение
_game_instance: GameNumber | None = None


def get_game_instance() -> GameNumber:
    """Возвращает единственный экземпляр GameNumber."""
    global _game_instance
    if _game_instance is None:
        _game_instance = GameNumber()
    return _game_instance