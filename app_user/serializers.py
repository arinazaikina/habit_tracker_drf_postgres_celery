import uuid
from typing import Dict, Any

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser
from .tasks import send_welcome_email_task


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Поля:
    - email: Строка с адресом электронной почты пользователя.
    - password: Строка с паролем пользователя.
    - password2: Строка с подтверждением пароля пользователя.
    - first_name: Строка с именем пользователя.
    - last_name: Строка с фамилией пользователя.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет валидность данных сериализатора.
        Возвращает входные данные сериализатора после проверки валидности.

        :param attrs: Входные данные сериализатора.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"error": "Passwords do not match"})

        return attrs

    def create(self, validated_data: Dict[str, Any]) -> CustomUser:
        """
        Создает новый экземпляр модели CustomUser с переданными данными.
        Устанавливает пароль пользователя.
        Сохраняет пользователя в базе данных.
        Отправляет пользователю приветственное письмо на указанный email
        со ссылкой на телеграмм-бот.

        :param validated_data: Валидированные данные сериализатора.
        """
        user = CustomUser.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            connection_code=uuid.uuid4().hex
        )

        user.set_password(validated_data['password'])
        user.save()

        send_welcome_email_task.delay(user.id)

        return user


class RegisterConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения регистрации пользователя
    через Telegram.
    """
    connection_code = serializers.CharField()
    telegram_id = serializers.IntegerField()


class RegisterCheckSerializer(serializers.Serializer):
    """
    Сериализатор для проверки завершения регистрации.
    """
    telegram_id = serializers.IntegerField()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя в списке публичных привычек"""

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email']
