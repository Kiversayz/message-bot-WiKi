import random


class GameNumber:
    def __init__ (self) -> None:
        self._game_data = {}
        self.lose_tries=5


    def _is_first_game(self,player_id: int) -> bool:
        if player_id not in self._game_data:
            return True
        return False

    def start_new_game(self, player_id: int, chat_id: int)-> int:
        if self._is_first_game(player_id):
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

    def check_game_status(self,player_id: int) -> bool:
        return self._game_data[player_id]['game_status']

    def _check_send_number(self,player_id: int, number: int) -> bool:
        self._game_data[player_id]['last_send_number'] = number
        return self._game_data[player_id]['number'] == number

    def _check_send_number_more (self, player_id: int, number: int) -> bool:
        if self._game_data[player_id]['last_send_number'] < number:
            return True
        return False

    def _check_lose(self,player_id: int) -> bool:
        return  self._game_data[player_id]['tries'] == self.lose_tries

    def _add_tries (self,player_id: int) -> None:
        self._game_data[player_id]['tries'] += 1

    def _end_game (self,player_id: int) -> None:
        self._game_data[player_id]['tries'] = 0
        self._game_data[player_id]['game_status'] = False
        self._game_data[player_id]['last_send_number'] = None

    def _end_game_lose(self,player_id: int) -> None:
        self._end_game(player_id)
        self._game_data[player_id]['losses'] += 1

    def _end_game_win(self,player_id: int) -> None:
        self._end_game(player_id)
        self._game_data[player_id]['wins'] += 1

    def last_send_number(self,player_id: int) -> int:
        return self._game_data[player_id]['last_send_number']

    def resume_game (self,player_id: int, send_number: int) -> str | None:
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
                return f'Не угада! {text_end}'





