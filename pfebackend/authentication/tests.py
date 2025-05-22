from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, Student, Teacher, Administrator
import jwt
from django.conf import settings

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test users with complete profiles
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

        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='admintest',
            password='pass123',
            first_name='Admin',
            last_name='Test',
            user_type='administrator',
            is_staff=True
        )
        self.admin = Administrator.objects.create(
            user=self.admin_user,
            role_description='System Administrator'
        )

    def test_student_login(self):
        """Test student login"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'student@test.com',
            'password': 'pass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_teacher_login(self):
        """Test teacher login"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'teacher@test.com',
            'password': 'pass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_admin_login(self):
        """Test administrator login"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'admin@test.com',
            'password': 'pass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'invalid@test.com',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test refresh token functionality"""
        # First get tokens through login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': 'student@test.com',
            'password': 'pass123'
        }
        login_response = self.client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']

        # Try to get new access token using refresh token
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_protected_endpoint_access(self):
        """Test accessing protected endpoint with token"""
        # First login to get token
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': 'student@test.com',
            'password': 'pass123'
        }
        login_response = self.client.post(login_url, login_data)
        token = login_response.data['access']

        # Try accessing protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        protected_url = reverse('user-profile', kwargs={'id': self.student_user.id})
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        protected_url = reverse('user-profile', kwargs={'id': self.student_user.id})
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PermissionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create users with different roles
        self.student = User.objects.create_user(
            email='student@test.com',
            username='student',
            password='pass123',
            user_type='student'
        )
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            username='teacher',
            password='pass123',
            user_type='teacher'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='pass123',
            user_type='administrator',
            is_staff=True
        )

    def test_student_permissions(self):
        """Test student access permissions"""
        self.client.force_authenticate(user=self.student)
        # Test access to student-specific endpoint
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_permissions(self):
        """Test teacher access permissions"""
        self.client.force_authenticate(user=self.teacher)
        # Test access to teacher-specific endpoint
        response = self.client.get(reverse('teacher-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_permissions(self):
        """Test admin access permissions"""
        self.client.force_authenticate(user=self.admin)
        # Test access to admin-specific endpoint
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        # Try accessing protected endpoint without authentication
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)