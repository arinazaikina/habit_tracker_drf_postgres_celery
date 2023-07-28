from unittest import TestCase, mock

from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from app_user.models import CustomUser
from app_user.services.email_service import EmailService
from app_user.tasks import send_welcome_email_task


class RegistrationAPITestCase(APITestCase):
    """Регистрация пользователя"""

    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """
        Проверка регистрации пользователя.
        - Новый пользователь создается в БД.
        - Пароль хешируется.
        - Назначается код для подключения к Telegram-боту.
        - ID пользователя в Telegram None
        - Статус прохождения регистрации False
        """
        url = '/api/register/'
        data = {
            "email": "ivan@mail.ru",
            "password": "qwerty123!",
            "password2": "qwerty123!",
            "first_name": "Ivan",
            "last_name": "Ivanov"
        }

        response = self.client.post(url, data, format='json')
        new_user = CustomUser.objects.get(email=data['email'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(new_user.id)
        self.assertTrue(new_user.check_password(data['password']))
        self.assertTrue(new_user.connection_code)
        self.assertFalse(new_user.tg_id)
        self.assertFalse(new_user.is_connected_to_tg)

    def test_user_registration_with_non_matching_passwords(self):
        """
        Проверка возврата статус-кода 400, если введенные пользователем пароли не совпали.
        :return:
        """
        url = '/api/register/'
        data = {
            "email": "max@mail.ru",
            "password": "qwerty123!",
            "password2": "qwerty567!",
            "first_name": "Maxim",
            "last_name": "Maximov"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegistrationConfirmAPITestCase(APITestCase):
    """Подтверждение регистрации"""

    def setUp(self):
        self.client = APIClient()
        self.test_email = 'ivan@mail.com'
        self.test_password = 'qwerty123!'
        self.test_first_name = 'Ivan'
        self.test_last_name = 'Ivanov'
        self.connection_code = '22f0c4d05bdf4033a3bab512e7e57a19'
        self.invalid_connection_code = 'invalid_code1234'
        self.telegram_id = 123456789
        self.user = CustomUser.objects.create_user(
            email=self.test_email,
            password=self.test_password,
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            connection_code=self.connection_code
        )
        self.url = '/api/register/confirm/'

    def test_confirm_registration(self):
        """
        Проверка подтверждения регистрации.
        Если передан корректный код подключения, то:
        - у пользователя сохраняется его ID в Telegram;
        - код подтверждения стирается (становится равным null);
        - флаг связывания с Telegram становится равным True.
        """
        data = {
            'connection_code': self.connection_code,
            'telegram_id': self.telegram_id,
        }
        response = self.client.post(self.url, data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.tg_id, self.telegram_id)
        self.assertFalse(self.user.connection_code)
        self.assertTrue(self.user.is_connected_to_tg)

    def test_confirm_registration_with_invalid_code(self):
        """
        Регистрация не подтверждена, если введен некорректный код подключения:
        - у пользователя не сохраняется его ID в Telegram;
        - код подтверждения не стирается;
        - флаг связывания с Telegram остается равным False.
        """
        data = {
            'connection_code': self.invalid_connection_code,
            'telegram_id': self.telegram_id,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotEqual(self.user.tg_id, self.telegram_id)
        self.assertTrue(self.user.connection_code)
        self.assertFalse(self.user.is_connected_to_tg)


class RegistrationCheckAPITestCase(APITestCase):
    """Проверка регистрации"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register/check/'

        self.user = CustomUser.objects.create(
            email='iavan@mail.ru',
            first_name='Ivan',
            last_name='Ivanov',
            connection_code=None,
            tg_id=1234567890,
            is_connected_to_tg=True
        )

    def test_check_registered_user(self):
        """
        Запрос к API с telegram_id созданного пользователя содержит в ответе is_connected = True.
        """
        data = {'telegram_id': self.user.tg_id}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['is_connected'])

    def test_check_not_registered_user(self):
        """
        Запрос к API с несуществующим telegram_id содержит в ответе is_connected = True.
        """
        data = {'telegram_id': 9876543210}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_connected'])


class CustomTokenObtainPairViewTestCase(APITestCase):
    """Проверка авторизации"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/login/'
        self.user_connected_to_tg = CustomUser.objects.create_user(
            email='anna@mail.ru',
            password='qwerty123!',
            is_connected_to_tg=True
        )
        self.user_not_connected_to_tg = CustomUser.objects.create_user(
            email='olga@mail.ru',
            password='qwerty123!',
            is_connected_to_tg=False
        )

    def test_login_with_user_connected_to_tg(self):
        """
        Проверка возможности залогиниться для пользователя, подключенного к Telegram.
        """
        data = {
            "email": self.user_connected_to_tg.email,
            "password": 'qwerty123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_login_with_user_not_connected_to_tg(self):
        """
        Проверка невозможности залогиниться для пользователя, не подключенного к Telegram.
        """
        data = {
            "email": self.user_not_connected_to_tg.email,
            "password": 'qwerty123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('access', response.data)
        self.assertEqual(response.data['error'], "Пользователь не подключен к Telegram")


class EmailServiceTest(TestCase):
    """Отправка письма"""

    def setUp(self):
        self.user = CustomUser.objects.create(
            email='ivan@mail.ru',
            first_name='Ivan',
            last_name='Ivanov',
            connection_code='1234567890',
        )

        self.email_service = EmailService()

    def test_send_welcome_email(self):
        """Тестирование отправки приветственного письма"""

        self.email_service.send_welcome_email(self.user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Добро пожаловать в наш трекер привычек!')


class TestCeleryTasks(TestCase):
    """Выполнение задачи celery на отправку письма"""

    def setUp(self):
        self.user = CustomUser.objects.create(
            email='max@mail.ru',
            first_name='Max',
            last_name='Maximov',
            connection_code='1234567890',
        )

    @mock.patch.object(EmailService, 'send_welcome_email')
    def test_send_welcome_email_task(self, mock_send_welcome_email):
        """
        Проверка выполнения задачи celery на отправку письма.
        Используется mock для имитации реальной функции send_welcome_email.
        Вызывается задача Celery send_welcome_email_task с id пользователя.
        Далее проверяется, что mock функция send_welcome_email была вызвана один раз
        и с правильными аргументами (с объектом пользователя, который создан в этом тесте).
        """
        send_welcome_email_task.apply(args=[self.user.id])
        mock_send_welcome_email.assert_called_once_with(self.user)
