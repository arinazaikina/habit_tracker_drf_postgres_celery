from celery import shared_task

from .models import CustomUser
from .services.email_service import EmailService


@shared_task
def send_welcome_email_task(user_id: int) -> None:
    """
    Задача Celery для отправки приветственного письма пользователю.
    Эта задача использует Celery для асинхронной отправки приветственного письма
    пользователю.

    :param user_id: ID пользователя, которому необходимо отправить приветственное письмо.
    """
    user = CustomUser.get_user_by_id(user_id)
    if user is not None:
        EmailService.send_welcome_email(user)
