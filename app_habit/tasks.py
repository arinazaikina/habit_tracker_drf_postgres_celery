import requests
from celery import shared_task

from config.settings import BOT_TOKEN
from .models import Habit


def send_message_to_user(user_tg_id: int, message: str) -> None:
    """
    Отправка сообщения пользователю в Telegram.
    :param user_tg_id: ID пользователя в Telegram
    :param message: Текст сообщения.
    :return:
    """
    token = BOT_TOKEN
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {'chat_id': user_tg_id, 'text': message}
    requests.post(url, data=data)


@shared_task
def send_reminder(habit_id: int) -> None:
    """
    Задача Celery для отправки напоминания пользователю.

    :param habit_id: ID привычки, для которой нужно отправить напоминание.
    """
    habit = Habit.objects.get(id=habit_id)
    user = habit.user
    message = (f"⏰ Пора выполнить привычку: {habit.action}\n"
               f"📍 {habit.place}\n")

    if habit.related_habit:
        message += f"После этого ты сможешь {habit.related_habit.action} 🙂\n"

    if habit.reward:
        message += f" 🎁 Твое вознаграждение: {habit.reward}"

    send_message_to_user(user.tg_id, message)
