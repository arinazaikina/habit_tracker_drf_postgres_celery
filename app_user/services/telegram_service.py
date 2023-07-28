from app_user.models import CustomUser


class TelegramService:
    """
    Сервис, описывающий работу с Telegram.
    """

    @staticmethod
    def link_telegram_account(user: CustomUser, tg_id: int) -> None:
        """
        Связывает аккаунт пользователя на сервисе привычек с Telegram-аккаунтом пользователя.
        При вызове этого метода в БД для пользователя сохраняется ID пользователя в Telegram,
        код подключения стирается (null), обновляется статус is_connected_to_tg (True).

        :param user: Объект CustomUser, для которого надо привязать аккаунт в Telegram.
        :param tg_id: ID пользователя в Telegram.
        """
        user.tg_id = tg_id
        user.connection_code = None
        user.is_connected_to_tg = True
        user.save()
