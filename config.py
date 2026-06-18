from dotenv import load_dotenv
import os

load_dotenv()  # Загружает все переменные из .env

TEG_USERNAME_TG_BOT = os.getenv('TEG_USERNAME_TG_BOT')
TOKEN_ACCESS_API_TG_BOT = os.getenv('TOKEN_ACCESS_API_TG_BOT')
API_CORE_TG = os.getenv('API_CORE_TG')
API_URL_TG = os.getenv('API_URL_TG')
API_CATS_URL = 'https://api.thecatapi.com/v1/images/search'
BASE_URL = f'{API_URL_TG}{TOKEN_ACCESS_API_TG_BOT}'