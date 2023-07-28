from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .models import Habit


class ReminderService:
    """Сервис, описывающий напоминания о привычках"""

    def __init__(self, habit: Habit) -> None:
        """
        Инициализация сервиса напоминаний.
        :param habit: Экземпляр модели Habit, для которого создается сервис напоминаний.
        """
        self.habit = habit

    def create_schedule(self) -> CrontabSchedule:
        """
        Создает и возвращает расписание CrontabSchedule
        для привычки на основе заданной периодичности и времени.
        """
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=self.habit.time.minute,
            hour=self.habit.time.hour,
            day_of_month=f'*/{self.habit.periodicity}',
            month_of_year='*',
            day_of_week='*',
        )
        return schedule

    def create_reminder(self) -> None:
        """
        Создает периодическую задачу (напоминание)
        для привычки на основе расписания.
        """
        task_name = f'reminder_for_habit_{self.habit.id}'
        task_func = 'app_habit.tasks.send_reminder'

        schedule = self.create_schedule()

        PeriodicTask.objects.create(
            crontab=schedule,
            name=task_name,
            task=task_func,
            args=[self.habit.id],
        )

    def create_test_schedule(self) -> CrontabSchedule:
        """
        Создает и возвращает тестовое расписание CrontabSchedule
        для привычки на основе заданной периодичности и времени.
        """
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=f'*/{self.habit.periodicity}',
            hour='*',
            day_of_month='*',
            month_of_year='*',
            day_of_week='*',
        )
        return schedule

    def create_test_reminder(self) -> None:
        """
        Создает тестовую периодическую задачу (напоминание)
        для привычки на основе расписания.
        """
        task_name = f'reminder_for_habit_{self.habit.id}'
        task_func = 'app_habit.tasks.send_reminder'

        schedule = self.create_test_schedule()

        PeriodicTask.objects.create(
            crontab=schedule,
            name=task_name,
            task=task_func,
            args=[self.habit.id],
        )

    def delete_reminder(self) -> None:
        """
        Удаляет периодическую задачу (напоминание) для привычки.
        """
        task_name = f'reminder_for_habit_{self.habit.id}'
        PeriodicTask.objects.filter(name=task_name).delete()

    def update_reminder(self) -> None:
        """
        Обновляет периодическую задачу (напоминание) для привычки.
        Удаляет текущее напоминание и создает новое.
        """
        self.delete_reminder()
        self.create_reminder()

    def update_test_reminder(self) -> None:
        """
        Обновляет тестовую периодическую задачу (напоминание) для привычки.
        Удаляет текущее напоминание и создает новое.
        """
        self.delete_reminder()
        self.create_test_reminder()
