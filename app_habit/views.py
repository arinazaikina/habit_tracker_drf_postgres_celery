from typing import List

from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Habit
from .serializers import HabitSerializer, PublicHabitSerializer
from .services import ReminderService


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 5


class HabitViewSet(viewsets.ModelViewSet):
    """
    ViewSet для привычек.
    Позволяет выполнять операции CRUD (создание, чтение, обновление, удаление) над привычками.
    """
    queryset = Habit.get_all_habits()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self) -> List[Habit]:
        """
        Возвращает QuerySet привычек в зависимости от аутентификации пользователя.
        QuerySet привычек ограничен только привычками текущего пользователя,
        если пользователь аутентифицирован.
        В противном случае возвращается пустой QuerySet.
        """
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return Habit.objects.none()

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Создание новой привычки и связанного с ней напоминания.

        :param request: HTTP-запрос.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        instance = Habit.objects.get(id=serializer.data['id'])
        reminder_service = ReminderService(instance)
        reminder_service.create_test_reminder()
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer: HabitSerializer) -> None:
        """
        Выполняет создание привычки и автоматически присваивает ее текущему пользователю.

        :param serializer: Сериализатор для привычки.
        """

        serializer.save(user=self.request.user)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Удаление привычки и связанного с ней напоминания.

        :param request: HTTP-запрос.
        """
        instance = self.get_object()
        reminder_service = ReminderService(instance)
        reminder_service.delete_reminder()
        return super().destroy(request, *args, **kwargs)

    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Обновление привычки и связанного с ней напоминания.

        :param request: HTTP-запрос.
        """
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            instance = self.get_object()
            reminder_service = ReminderService(instance)
            reminder_service.update_test_reminder()
        return response

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        """
        Частичное обновление привычки и связанного с ней напоминания.

        :param request: HTTP-запрос.
        """
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            instance = self.get_object()
            reminder_service = ReminderService(instance)
            reminder_service.update_test_reminder()
        return response


class PublicHabitsAPIView(ListAPIView):
    """Просмотр списка публичных привычек"""
    serializer_class = PublicHabitSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self) -> List[Habit]:
        """
        Возвращает QuerySet публичных привычек.
        """
        return Habit.objects.filter(is_public=True).order_by('id')
