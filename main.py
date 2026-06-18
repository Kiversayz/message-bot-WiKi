import requests
import time
from config import *

if __name__ == '__main__':
    MAX_COUNTER=100
    TEXT='Я получил твое сообщение, солнышко!'
    offset = -2
    counter = 0
    chat_id: int
    base_url = BASE_URL
    ERROR_TEXT = 'Здесь должна была быть картинка с котиком :('
    cat_response: requests.Response
    cat_link: str

    while counter < MAX_COUNTER:

        print('attempt =', counter)  #Чтобы видеть в консоли, что код живет

        updates = requests.get(f'{base_url}/getUpdates?offset={offset + 1}').json()

        if updates['result']:
            for result in updates['result']:
                offset = result['update_id']
                chat_id = result['message']['from']['id']

                cat_response = requests.get(API_CATS_URL)
                if cat_response.status_code == 200:
                    cat_link = cat_response.json()[0]['url']
                    requests.get(f'{base_url}/sendMessage?chat_id={chat_id}&text={TEXT}')
                    requests.get(f'{base_url}/sendPhoto?chat_id={chat_id}&photo={cat_link}')
                else:
                    requests.get(f'{base_url}/sendMessage?chat_id={chat_id}&text={ERROR_TEXT}')

        time.sleep(1)
        counter += 1