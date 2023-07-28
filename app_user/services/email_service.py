import logging

from django.conf import settings
from django.core.mail import send_mail

from app_user.models import CustomUser

logger = logging.getLogger(__name__)


class EmailService:
    """
    Сервис, описывающий отправку писем.
    """

    @staticmethod
    def send_welcome_email(user: CustomUser) -> None:
        """
        Отправляет приветственное письмо новому пользователю.
        В письме отправляется ссылка на Telegram-бот и код для подключения.

        :param user: Объект пользователя, которому необходимо отправить письмо.
        """
        user_name = user.first_name if user.first_name else user.email
        subject = "Добро пожаловать в наш трекер привычек!"
        message = f"Привет, {user.first_name}!\n" \
                  f"Спасибо за регистрацию.\nПожалуйста, перейдите по следующей ссылке, " \
                  f"чтобы начать взаимодействовать с нашим ботом в Telegram: https://t.me/SkyproHabitTrackerBot\n" \
                  f"Для подключения к боту используйте код {user.connection_code}"
        from_email = settings.EMAIL_HOST_USER
        to_list = [user.email]

        try:
            logger.info(f'Отправка письма для {user_name}')
            send_mail(subject, message, from_email, to_list, fail_silently=True)
        except Exception as error:
            logger.error(f'Ошибка отправки письма: {error}')
