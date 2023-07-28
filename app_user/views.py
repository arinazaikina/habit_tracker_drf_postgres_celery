from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import RegisterUserSerializer, RegisterConfirmSerializer, RegisterCheckSerializer
from .services.telegram_service import TelegramService


class RegisterView(generics.CreateAPIView):
    """Регистрация пользователя"""
    queryset = CustomUser.get_all_users()
    permission_classes = (AllowAny,)
    serializer_class = RegisterUserSerializer


class RegisterConfirmView(APIView):
    """Подтверждение регистрации через Telegram"""
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="This endpoint is for confirming registration",
        request_body=RegisterConfirmSerializer,
        responses={
            200: 'Telegram account successfully linked',
            404: 'User with this connection code does not exist'
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = RegisterConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = CustomUser.get_user_by_connection_code(serializer.validated_data['connection_code'])

        if user:
            TelegramService.link_telegram_account(user, serializer.validated_data['telegram_id'])
            return Response({"detail": "Telegram account successfully linked"}, status=status.HTTP_200_OK)
        return Response({"detail": "User with this connection code does not exist"}, status=status.HTTP_404_NOT_FOUND)


class RegisterCheckView(APIView):
    """Проверка статуса регистрации"""
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_description="This endpoint checks if the user is registered",
        request_body=RegisterCheckSerializer,
        responses={200: 'Returns a JSON object with "is_connected" boolean field'},
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = RegisterCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_id = serializer.validated_data['telegram_id']
        user = CustomUser.objects.filter(tg_id=telegram_id).first()

        if user and user.is_connected_to_tg:
            return Response({"is_connected": True}, status=status.HTTP_200_OK)
        return Response({"is_connected": False}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Авторизация"""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken:
            raise AuthenticationFailed("Неверные учетные данные")

        user = serializer.user
        if not user.is_connected_to_tg:
            return Response({"error": "Пользователь не подключен к Telegram"},
                            status=status.HTTP_401_UNAUTHORIZED)

        return super().post(request, *args, **kwargs)
