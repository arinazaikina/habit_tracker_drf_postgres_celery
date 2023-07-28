import os

import aiohttp
from aiogram.types import Message
from dotenv import load_dotenv

from bot import dp

load_dotenv()
SERVER_URL = os.getenv('DJANGO_SERVER_URL')


@dp.message_handler(commands=['start'])
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start.
    Этот обработчик вызывается, когда пользователь отправляет команду /start Telegram-боту.

    :param message: Объект типа Message.
    """
    telegram_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        data = {"telegram_id": telegram_id}
        async with session.post(f'{SERVER_URL}/api/register/check/', json=data) as response:
            data = await response.json()
            if data['is_connected']:
                await message.answer("Вы уже подключили свой аккаунт к телеграмму!")
            else:
                await message.answer(
                    'Привет! Я твой бот, готов помочь тебе с привычками. Для начала введи код подключения!'
                )


@dp.message_handler()
async def process_connection_code(message: Message) -> None:
    """
     Обработчик кода подключения.
     Этот обработчик вызывается, когда пользователь отправляет код подключения Telegram-боту.

     :param message: Объект типа Message.

     """
    connection_code = message.text
    telegram_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{SERVER_URL}/api/register/confirm/',
                                data={'connection_code': connection_code, 'telegram_id': telegram_id}) as response:
            if response.status == 200:
                await message.answer("Ваш аккаунт успешно связан с телеграммом!")
            else:
                await message.answer(
                    "Произошла ошибка при связывании аккаунта. "
                    "Пожалуйста, проверьте код подключения и попробуйте снова."
                )
