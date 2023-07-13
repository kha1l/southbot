from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher


class Config:
    load_dotenv()
    dbase = os.getenv('DATA_BASE')
    user = os.getenv('USER_NAME')
    password = os.getenv('PASSWORD')
    host = os.getenv('IP')
    token = os.getenv('TOKEN')
    bot = Bot(token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=MemoryStorage())
    scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
    bot_pyrus = os.getenv('BOT_PYRUS')
    key = os.getenv('KEY')
    client = os.getenv('CLIENT')
    redirect = os.getenv('REDIRECT')
    secret = os.getenv('SECRET')
    verifier = os.getenv('VERIFIER')
