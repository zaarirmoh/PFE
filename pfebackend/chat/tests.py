from django.test import TestCase
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Student, Teacher
from teams.models import Team, TeamMembership
from chat.models import ChatRoom, Message
from chat.routing import websocket_urlpatterns
from chat.consumers import ChatConsumer
import json

class ChatTests(TestCase):
    def setUp(self):
        # Create teacher with complete profile
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )

        # Create student with complete profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_MEMBER
        )

        # Create chat room
        self.chat_room = ChatRoom.objects.create(
            team=self.team,
            name="Team Chat"
        )
        self.chat_room.participants.add(self.teacher_user, self.student_user)

    def test_chat_room_creation(self):
        """Test chat room creation and basic attributes"""
        self.assertEqual(self.chat_room.name, "Team Chat")
        self.assertEqual(self.chat_room.team, self.team)
        self.assertEqual(self.chat_room.participants.count(), 2)
        self.assertIn(self.teacher_user, self.chat_room.participants.all())
        self.assertIn(self.student_user, self.chat_room.participants.all())

    def test_message_creation(self):
        """Test message creation in chat room"""
        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.student_user,
            content="Hello, teacher!"
        )
        self.assertEqual(message.sender, self.student_user)
        self.assertEqual(message.content, "Hello, teacher!")
        self.assertIsNotNone(message.timestamp)

class ChatAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create teacher with complete profile
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )

        # Create student with complete profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_MEMBER
        )

        # Create chat room
        self.chat_room = ChatRoom.objects.create(
            team=self.team,
            name="Team Chat"
        )
        self.chat_room.participants.add(self.teacher_user, self.student_user)

        self.client.force_authenticate(user=self.student_user)

    def test_chat_room_list_api(self):
        """Test chat room listing endpoint"""
        url = reverse('chatroom-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_message_send_api(self):
        """Test sending message through API"""
        url = reverse('message-create')
        message_data = {
            'chat_room': self.chat_room.id,
            'content': 'Hello from API test!'
        }
        response = self.client.post(url, message_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().content, 'Hello from API test!')

    def test_message_list_api(self):
        """Test message listing endpoint"""
        # Create some messages first
        Message.objects.create(
            chat_room=self.chat_room,
            sender=self.student_user,
            content="Message 1"
        )
        Message.objects.create(
            chat_room=self.chat_room,
            sender=self.teacher_user,
            content="Message 2"
        )

        url = reverse('message-list', kwargs={'chat_room_id': self.chat_room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)