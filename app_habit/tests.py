from unittest.mock import patch

from django_celery_beat.models import PeriodicTask
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from app_habit.models import Habit
from app_habit.tasks import send_reminder
from app_user.models import CustomUser


class BaseTestCase(APITestCase):
    """
    Базовые настройки тест-кейса.
    Создание пользователей.
    Создание клиента для каждого пользователя.
    Аутентификация пользователей.
    """
    users_data = [
        {"email": "iavan@mail.ru", "password": "qwerty123!"},
        {"email": "max@mail.ru", "password": "qwerty123!"}
    ]

    @staticmethod
    def create_authenticated_client(user_data):
        client = APIClient()
        login = client.post('/api/login/', {'email': user_data['email'], 'password': user_data['password']})
        access_token = login.json().get('access')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return client

    def setUp(self):
        self.user_1 = CustomUser.objects.create_user(
            email='iavan@mail.ru',
            password='qwerty123!',
            first_name='Ivan',
            last_name='Ivanov',
            connection_code=None,
            tg_id=1234567890,
            is_connected_to_tg=True
        )
        self.user_2 = CustomUser.objects.create_user(
            email='max@mail.ru',
            password='qwerty123!',
            first_name='Max',
            last_name='Maximov',
            connection_code=None,
            tg_id=14567832,
            is_connected_to_tg=True
        )
        self.user_clients = []
        for user_data in self.users_data:
            client = self.create_authenticated_client(user_data)
            self.user_clients.append(client)


class HabitCreateAPITestCase(BaseTestCase):
    """Создание привычки"""

    def setUp(self):
        super().setUp()
        self.pleasant_habit = Habit.objects.create(
            place="Работа",
            time="09:00",
            action='Утренний кофе',
            is_pleasant=True,
            periodicity=1,
            time_for_action=120,
            is_public=False,
            user=self.user_1
        )

        self.not_pleasant_habit = Habit.objects.create(
            place="Работа",
            time="10:00",
            action='Проверка рабочей почты',
            is_pleasant=False,
            periodicity=1,
            time_for_action=120,
            is_public=True,
            user=self.user_1
        )
        self.url = '/api/habits/'

    def test_creating_habit_with_reward_and_related_habit(self):
        """
        Нельзя одновременно указать связанную привычку и вознаграждение.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "reward": "Конфета",
            "time_for_action": 60,
            "is_public": True,
            "related_habit": self.pleasant_habit.id
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'Нельзя одновременно указать связанную привычку и вознаграждение')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_habit_with_large_time_for_action(self):
        """
        Время выполнения привычки не может быть больше 120 секунд.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "reward": "Конфета",
            "time_for_action": 121,
            "is_public": True
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'Время выполнения должно быть не больше 120 секунд')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_pleasant_habit_with_reward(self):
        """
        У приятной привычки не может быть вознаграждения.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Утренний кофе",
            "is_pleasant": True,
            "periodicity": 1,
            "reward": "Конфета",
            "time_for_action": 100,
            "is_public": True,
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'У приятной привычки не может быть вознаграждения или связанной привычки')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_pleasant_habit_with_related_habit(self):
        """
        У приятной привычки не может быть связанной привычки.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Утренний кофе",
            "is_pleasant": True,
            "periodicity": 1,
            "time_for_action": 100,
            "is_public": True,
            "related_habit": self.pleasant_habit.id
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'У приятной привычки не может быть вознаграждения или связанной привычки')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_habit_with_large_periodicity(self):
        """
        Нельзя создать привычку с периодичностью более 7 дней.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 8,
            "reward": "Конфета",
            "time_for_action": 60,
            "is_public": True
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'Периодичность не может быть более 7 дней')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_habit_with_same_action(self):
        """
        Нельзя создать уже существующую привычку (проверка по действию).
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Утренний кофе",
            "is_pleasant": True,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('non_field_errors')[0],
                         'У вас уже есть привычка с таким действием')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creating_habit_with_not_pleasant_related_habit(self):
        """
        В качестве связанной не может выступать привычка без признака приятной.
        """
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 8,
            "time_for_action": 60,
            "is_public": True,
            "related_habit": self.not_pleasant_habit.id
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        self.assertEqual(response_data.get('related_habit')[0],
                         'В связанные привычки могут попадать только привычки с признаком приятной привычки')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_cannot_create_habit(self):
        """Неавторизованный пользователь не может создать привычку"""
        data = {
            "place": "Работа",
            "time": "09:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True
        }

        client = APIClient()
        response = client.post(self.url, data)
        response_data = response.json()

        self.assertEqual(response_data.get('detail'), 'Учетные данные не были предоставлены.')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_success_create_habit(self):
        """Успешное создание привычки и периодического напоминания"""
        data = {
            "place": "Работа",
            "time": "09:00:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True,
            "related_habit": self.pleasant_habit.id
        }
        response = self.user_clients[0].post(self.url, data)
        response_data = response.json()
        habits = self.user_clients[0].get(self.url).json().get('results')
        habit = Habit.objects.get(id=response_data.get('id'))
        periodic_tasks = PeriodicTask.objects.filter(
            args__contains=str(habit.id))
        task = periodic_tasks[0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response_data.get('id'))
        self.assertEqual(response_data.get('place'), data.get('place'))
        self.assertEqual(response_data.get('time'), data.get('time'))
        self.assertEqual(response_data.get('action'), data.get('action'))
        self.assertEqual(response_data.get('is_pleasant'), data.get('is_pleasant'))
        self.assertEqual(response_data.get('periodicity'), data.get('periodicity'))
        self.assertEqual(response_data.get('time_for_action'), data.get('time_for_action'))
        self.assertEqual(response_data.get('is_public'), data.get('is_public'))
        self.assertEqual(response_data.get('related_habit'), data.get('related_habit'))
        self.assertEqual(response_data.get('user'), self.user_1.id)
        self.assertEqual(len(habits), 3)

        self.assertEqual(len(periodic_tasks), 1)
        self.assertEqual(task.name, f"reminder_for_habit_{response_data.get('id')}")


class HabitReadAPITestCase(BaseTestCase):
    """Чтение привычки"""

    def setUp(self):
        super().setUp()
        self.url = '/api/habits/'
        data = {
            "place": "Работа",
            "time": "09:00:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True
        }

        self.habit_ids = []

        for user_client in self.user_clients:
            response = user_client.post(self.url, data)
            response_data = response.json()
            self.habit_ids.append(response_data.get('id'))

    def test_read_list_of_user_habits(self):
        """
        Пользователь видит список своих привычек.
        """
        for user_client in self.user_clients:
            response = user_client.get(self.url)
            response_data = response.json()

            self.assertEqual(len(response_data.get('results')), 1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_read_his_habit(self):
        """
        Пользователь видит детали своей привычки по ID.
        """
        for i, user_client in enumerate(self.user_clients):
            habit_id = self.habit_ids[i]
            response = user_client.get(f"{self.url}{habit_id}/")
            response_data = response.json()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data.get('id'), habit_id)
            self.assertIsNotNone(response_data.get('place'))
            self.assertIsNotNone(response_data.get('time'))
            self.assertIsNotNone(response_data.get('action'))
            self.assertIsNotNone(response_data.get('is_pleasant'))
            self.assertIsNotNone(response_data.get('periodicity'))
            self.assertIsNotNone(response_data.get('time_for_action'))
            self.assertIsNotNone(response_data.get('is_public'))

    def test_user_cannot_read_other_users_habit(self):
        """
        Пользователь не может видеть детали чужой привычки по ID.
        """
        user_client_1 = self.user_clients[0]
        other_users_habit_id = self.habit_ids[1]
        response = user_client_1.get(f"{self.url}{other_users_habit_id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HabitUpdateAPITestCase(BaseTestCase):
    """Обновление привычки"""

    def setUp(self):
        super().setUp()
        self.url = '/api/habits/'
        data = {
            "place": "Работа",
            "time": "09:00:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True
        }

        self.habit_ids = []

        for user_client in self.user_clients:
            response = user_client.post(self.url, data)
            response_data = response.json()
            self.habit_ids.append(response_data.get('id'))

    def test_user_can_edit_his_habit(self):
        """
        Пользователь может редактировать свою привычку по ID.
        Также изменяется и связанная с привычкой периодическая задача.
        """
        new_habit_data = {
            "place": "Дом",
            "time": "18:00:00",
            "action": "Читать книгу",
            "is_pleasant": True,
            "periodicity": 2,
            "time_for_action": 30,
            "is_public": False
        }

        for i, user_client in enumerate(self.user_clients):
            habit_id = self.habit_ids[i]
            response = user_client.put(f"{self.url}{habit_id}/", new_habit_data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response_data = response.json()
            task = PeriodicTask.objects.get(name=f"reminder_for_habit_{habit_id}")

            self.assertEqual(response_data.get('place'), new_habit_data.get('place'))
            self.assertEqual(response_data.get('time'), new_habit_data.get('time'))
            self.assertEqual(response_data.get('action'), new_habit_data.get('action'))
            self.assertEqual(response_data.get('is_pleasant'), new_habit_data.get('is_pleasant'))
            self.assertEqual(response_data.get('periodicity'), new_habit_data.get('periodicity'))
            self.assertEqual(response_data.get('time_for_action'), new_habit_data.get('time_for_action'))
            self.assertEqual(response_data.get('is_public'), new_habit_data.get('is_public'))
            self.assertEqual(task.crontab.minute, f'*/{new_habit_data["periodicity"]}')

    def test_user_cannot_edit_other_users_habit(self):
        """
        Пользователь не может редактировать чужую привычку по ID.
        """
        new_habit_data = {
            "place": "Дом",
            "time": "18:00:00",
            "action": "Читать книгу",
            "is_pleasant": True,
            "periodicity": 2,
            "time_for_action": 30,
            "is_public": False
        }

        user_client_1 = self.user_clients[0]
        other_users_habit_id = self.habit_ids[1]
        response = user_client_1.put(f"{self.url}{other_users_habit_id}/", new_habit_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_partially_update_his_habit(self):
        """
        Пользователь может частично обновить свою привычку по ID.
        Также изменяется и связанная с привычкой периодическая задача.
        """
        new_habit_data = {"place": "Дом", "periodicity": 4}

        for i, user_client in enumerate(self.user_clients):
            habit_id = self.habit_ids[i]
            response = user_client.patch(f"{self.url}{habit_id}/", new_habit_data)
            response_data = response.json()
            task = PeriodicTask.objects.get(name=f"reminder_for_habit_{habit_id}")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data.get('place'), new_habit_data.get('place'))
            self.assertEqual(task.crontab.minute, f'*/{new_habit_data["periodicity"]}')

    def test_user_cannot_partially_update_other_users_habit(self):
        """
        Пользователь не может частично обновить чужую привычку по ID
        """
        new_habit_data = {"place": "Дом"}

        user_client_1 = self.user_clients[0]
        other_users_habit_id = self.habit_ids[1]
        response = user_client_1.patch(f"{self.url}{other_users_habit_id}/", new_habit_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HabitDeleteAPITestCase(BaseTestCase):
    """Удаление привычки"""

    def setUp(self):
        super().setUp()
        self.url = '/api/habits/'
        data = {
            "place": "Работа",
            "time": "09:00:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
            "is_public": True
        }

        self.habit_ids = []

        for user_client in self.user_clients:
            response = user_client.post(self.url, data)
            response_data = response.json()
            self.habit_ids.append(response_data.get('id'))

    def test_user_can_delete_own_habit(self):
        """
        Пользователь может удалить свою привычку.
        Также удаляется связанная с ней периодическая задача о напоминании.
        """
        for i, user_client in enumerate(self.user_clients):
            response = user_client.delete(f"{self.url}{self.habit_ids[i]}/")

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(Habit.objects.filter(id=self.habit_ids[i]).exists())
            self.assertFalse(PeriodicTask.objects.filter(name=f"reminder_for_habit_{self.habit_ids[i]}").exists())

    def test_user_cannot_delete_other_user_habit(self):
        """Пользователь не может удалить чужую привычку"""
        for i in range(len(self.user_clients) - 1):
            response = self.user_clients[i].delete(f"{self.url}{self.habit_ids[i + 1]}/")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertTrue(Habit.objects.filter(id=self.habit_ids[i + 1]).exists())


class PublicHabitsListAPITestCase(BaseTestCase):
    """Просмотр публичных привычек"""

    def setUp(self):
        super().setUp()
        self.url = '/api/habits/public'
        self.habit_data = {
            "place": "Работа",
            "time": "09:00:00",
            "action": "Почистить спам",
            "is_pleasant": False,
            "periodicity": 1,
            "time_for_action": 60,
        }

    def create_habit(self, user, is_public):
        habit_data = self.habit_data.copy()
        habit_data['user'] = user
        habit_data['is_public'] = is_public
        return Habit.objects.create(**habit_data)

    def test_public_habits_list(self):
        """Всем авторизованным пользователям доступен список публичных привычек"""
        self.create_habit(self.user_1, is_public=True)
        self.create_habit(self.user_1, is_public=True)
        self.create_habit(self.user_2, is_public=False)

        response = self.user_clients[0].get(self.url)
        response_data = response.json().get('results')
        first_habit = response.json().get('results')[0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 2)
        self.assertIn('user', first_habit)
        self.assertEqual(first_habit['user']['id'], self.user_1.id)
        self.assertEqual(first_habit['user']['email'], self.user_1.email)
        self.assertEqual(first_habit['user']['first_name'], self.user_1.first_name)
        self.assertEqual(first_habit['user']['last_name'], self.user_1.last_name)


class SendReminderTestCase(APITestCase):
    """Отправка напоминания"""

    @patch('app_habit.models.Habit.objects.get')
    @patch('app_habit.tasks.send_message_to_user')
    def test_send_reminder(self, mock_send_message, mock_habit_get):
        """Функция отправки напоминания вызывается с правильным сообщением"""
        mock_habit = mock_habit_get.return_value
        mock_habit.action = "Тестовая привычка"
        mock_habit.place = "Тестовое место"
        mock_habit.related_habit = None
        mock_habit.reward = "Тестовое вознаграждение"
        mock_habit.user.tg_id = 123456789

        send_reminder(1)

        message = ("⏰ Пора выполнить привычку: Тестовая привычка\n"
                   "📍 Тестовое место\n "
                   "🎁 Твое вознаграждение: Тестовое вознаграждение")

        mock_send_message.assert_called_once_with(123456789, message)
