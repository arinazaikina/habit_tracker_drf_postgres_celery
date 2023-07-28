from typing import List

from django.db import models

from app_user.models import CustomUser

NULLABLE = {'blank': True, 'null': True}


class Habit(models.Model):
    """Модель, описывающая привычку"""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    place = models.CharField(max_length=200, verbose_name='Место')
    time = models.TimeField(verbose_name='Время')
    action = models.CharField(max_length=200, verbose_name='Действие')
    is_pleasant = models.BooleanField(verbose_name='Признак приятной привычки')
    related_habit = models.ForeignKey('self', on_delete=models.SET_NULL, **NULLABLE,
                                      verbose_name='Связанная привычка')
    periodicity = models.IntegerField(default=1, verbose_name='Периодичность в днях')
    reward = models.CharField(max_length=200, verbose_name='Вознаграждение', **NULLABLE)
    time_for_action = models.PositiveIntegerField(verbose_name='Время на выполнение')
    is_public = models.BooleanField(default=False, verbose_name='Признак публичности')

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        db_table = 'habits'

    def __str__(self):
        return f'{self.action}'

    @classmethod
    def get_all_habits(cls) -> List['CustomUser']:
        """
        Возвращает список всех привычек
        """
        return cls.objects.all().order_by('id')
