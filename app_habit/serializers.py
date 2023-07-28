from typing import Dict, Any

from rest_framework import serializers

from app_user.serializers import UserSerializer
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = '__all__'
        read_only_fields = ('user',)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверка валидности данных запроса:
        - нельзя одновременно указать связанную привычку и вознаграждение;
        - время выполнения не больше 120 секунд;
        - у приятной привычки не может быть вознаграждения или связанной привычки;
        - периодичность не может быть более 7 дней;
        :param data: Входные данные для создания/обновления привычки.
        """
        user = self.context['request'].user

        if data.get('reward') and data.get('related_habit'):
            raise serializers.ValidationError(
                'Нельзя одновременно указать связанную привычку и вознаграждение'
            )

        if 'time_for_action' in data and data['time_for_action'] > 120:
            raise serializers.ValidationError('Время выполнения должно быть не больше 120 секунд')

        if 'is_pleasant' in data and data['is_pleasant'] and (data.get('reward') or data.get('related_habit')):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки"
            )

        if 'periodicity' in data and data['periodicity'] > 7:
            raise serializers.ValidationError('Периодичность не может быть более 7 дней')

        if 'action' in data and Habit.objects.filter(action=data['action'], user=user).exists():
            raise serializers.ValidationError('У вас уже есть привычка с таким действием')

        return data

    @staticmethod
    def validate_related_habit(value: Habit) -> Habit:
        """
        Проверка, что в связанные привычки могут попадать только привычки с признаком приятной привычки.
        :param value: Связанная привычка.
        """
        if not value.is_pleasant:
            raise serializers.ValidationError(
                'В связанные привычки могут попадать только привычки с признаком приятной привычки'
            )
        return value

    def create(self, validated_data: Dict[str, Any]) -> Habit:
        """
        Создание новой привычки.
        :param validated_data: Валидные данные для создания привычки.
        """
        validated_data['user'] = self.context['request'].user
        habit = super().create(validated_data)
        return habit


class PublicHabitSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных в списке публичных привычек"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Habit
        fields = ['user', 'place', 'time', 'action', 'is_pleasant', 'related_habit',
                  'periodicity', 'reward', 'time_for_action', 'is_public']
