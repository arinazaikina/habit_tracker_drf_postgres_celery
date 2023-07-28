from typing import List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager

NULLABLE = {'blank': True, 'null': True}


class CustomUser(AbstractUser):
    """
    Модель, описывающая пользователя.
    Наследуется от AbstractUser.
    """
    objects = CustomUserManager()

    username = None
    email = models.EmailField(unique=True, verbose_name='Электронная почта')
    connection_code = models.CharField(max_length=36, **NULLABLE, verbose_name='Уникальный код подключения')
    tg_id = models.IntegerField(**NULLABLE, verbose_name='ID пользователя в телеграмме')
    is_connected_to_tg = models.BooleanField(default=False, verbose_name='Подключен к Telegram')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @classmethod
    def get_all_users(cls) -> List['CustomUser']:
        """
        Возвращает список всех пользователей
        """
        return cls.objects.all()

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional['CustomUser']:
        """
        Возвращает пользователя по его ID или None,
        если пользователь не найден.
        """
        try:
            return cls.objects.get(id=user_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_user_by_connection_code(cls, connection_code: str) -> Optional['CustomUser']:
        """
        Возвращает пользователя по его коду подключения или None,
        если пользователь не найден.
        """
        try:
            return cls.objects.get(connection_code=connection_code)
        except cls.DoesNotExist:
            return None
