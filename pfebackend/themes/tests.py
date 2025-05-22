from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from themes.models import Theme, ThemeChoice
from django.utils import timezone

class ThemeTests(TestCase):
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

        # Create theme
        self.theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            creator=self.teacher_user,
            academic_year="4siw",
            max_students=4
        )

    def test_theme_creation(self):
        """Test theme creation and basic attributes"""
        self.assertEqual(self.theme.title, "Test Theme")
        self.assertEqual(self.theme.creator, self.teacher_user)
        self.assertEqual(self.theme.max_students, 4)

    def test_theme_choice_creation(self):
        """Test theme choice creation"""
        theme_choice = ThemeChoice.objects.create(
            theme=self.theme,
            student=self.student,
            priority=1
        )
        self.assertEqual(theme_choice.theme, self.theme)
        self.assertEqual(theme_choice.student, self.student)
        self.assertEqual(theme_choice.priority, 1)

class ThemeAPITests(APITestCase):
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

        self.client.force_authenticate(user=self.teacher_user)

    def test_create_theme_api(self):
        """Test theme creation through API"""
        url = reverse('theme-create')
        data = {
            'title': 'API Test Theme',
            'description': 'Theme created through API',
            'academic_year': '4siw',
            'max_students': 4,
            'technologies': ['Python', 'Django'],
            'requirements': ['Good programming skills']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Theme.objects.count(), 1)
        theme = Theme.objects.first()
        self.assertEqual(theme.title, 'API Test Theme')
        self.assertEqual(theme.creator, self.teacher_user)

    def test_theme_list_api(self):
        """Test theme listing endpoint"""
        # Create some themes first
        Theme.objects.create(
            title="Theme 1",
            description="First test theme",
            creator=self.teacher_user,
            academic_year="4siw",
            max_students=4
        )
        Theme.objects.create(
            title="Theme 2",
            description="Second test theme",
            creator=self.teacher_user,
            academic_year="4siw",
            max_students=3
        )

        url = reverse('theme-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_theme_choice_api(self):
        """Test theme choice creation through API"""
        theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            creator=self.teacher_user,
            academic_year="4siw",
            max_students=4
        )
        
        # Switch to student user for theme choice
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('theme-choice-create')
        data = {
            'theme': theme.id,
            'priority': 1
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ThemeChoice.objects.count(), 1)
        theme_choice = ThemeChoice.objects.first()
        self.assertEqual(theme_choice.student, self.student)
        self.assertEqual(theme_choice.priority, 1)

    def test_theme_detail_api(self):
        """Test theme detail retrieval"""
        theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            creator=self.teacher_user,
            academic_year="4siw",
            max_students=4
        )

        url = reverse('theme-detail', kwargs={'pk': theme.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Theme')
        self.assertEqual(response.data['creator']['id'], self.teacher_user.id)
