from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Student, Teacher
from teams.models import Team, TeamMembership
from notifications.models import Notification, NotificationCategory

class NotificationTests(TestCase):
    def setUp(self):
        # Create sender (teacher) with complete profile
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

        # Create recipient (student) with complete profile
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

        # Create notification category
        self.category = NotificationCategory.objects.create(
            name="Meeting",
            description="Meeting related notifications"
        )

        # Create notification
        self.notification = Notification.objects.create(
            sender=self.teacher_user,
            recipient=self.student_user,
            category=self.category,
            title="Meeting Scheduled",
            message="Project progress meeting scheduled for tomorrow",
            is_read=False
        )

    def test_notification_creation(self):
        """Test notification creation and basic attributes"""
        self.assertEqual(self.notification.sender, self.teacher_user)
        self.assertEqual(self.notification.recipient, self.student_user)
        self.assertEqual(self.notification.category, self.category)
        self.assertFalse(self.notification.is_read)

    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)

class NotificationAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create sender (teacher) with complete profile
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

        # Create recipient (student) with complete profile
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

        # Create notification category
        self.category = NotificationCategory.objects.create(
            name="Meeting",
            description="Meeting related notifications"
        )

        self.client.force_authenticate(user=self.student_user)

    def test_notification_list_api(self):
        """Test notification listing endpoint"""
        # Create some notifications
        Notification.objects.create(
            sender=self.teacher_user,
            recipient=self.student_user,
            category=self.category,
            title="Notification 1",
            message="Test message 1"
        )
        Notification.objects.create(
            sender=self.teacher_user,
            recipient=self.student_user,
            category=self.category,
            title="Notification 2",
            message="Test message 2"
        )

        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_notification_mark_read_api(self):
        """Test marking notification as read through API"""
        notification = Notification.objects.create(
            sender=self.teacher_user,
            recipient=self.student_user,
            category=self.category,
            title="Test Notification",
            message="Test message"
        )

        url = reverse('notification-mark-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_notification_bulk_mark_read_api(self):
        """Test marking multiple notifications as read through API"""
        # Create multiple unread notifications
        notifications = [
            Notification.objects.create(
                sender=self.teacher_user,
                recipient=self.student_user,
                category=self.category,
                title=f"Notification {i}",
                message=f"Test message {i}"
            ) for i in range(3)
        ]

        url = reverse('notification-bulk-mark-read')
        notification_ids = [n.id for n in notifications]
        response = self.client.post(url, {'notification_ids': notification_ids})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all notifications are marked as read
        for notification in Notification.objects.filter(id__in=notification_ids):
            self.assertTrue(notification.is_read)