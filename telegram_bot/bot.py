import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
