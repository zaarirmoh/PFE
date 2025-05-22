from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Student, Teacher, Administrator, ExternalUser, StudentSkill
from django.utils import timezone

class UserModelTests(TestCase):
    def test_student_creation(self):
        """Test student user creation with all required fields"""
        student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        student = Student.objects.create(
            user=student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )
        
        self.assertEqual(student_user.email, 'student@test.com')
        self.assertEqual(student_user.user_type, 'student')
        self.assertEqual(student.matricule, '12345')
        self.assertEqual(student.current_year, '4siw')

    def test_teacher_creation(self):
        """Test teacher user creation with all required fields"""
        teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            user_type='teacher'
        )
        teacher = Teacher.objects.create(
            user=teacher_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )
        
        self.assertEqual(teacher_user.email, 'teacher@test.com')
        self.assertEqual(teacher_user.user_type, 'teacher')
        self.assertEqual(teacher.department, 'Computer Science')
        self.assertEqual(teacher.grade, 'maitre_assistant_b')

    def test_admin_creation(self):
        """Test administrator user creation with all required fields"""
        admin_user = User.objects.create_user(
            email='admin@test.com',
            username='admintest',
            password='pass123',
            first_name='Admin',
            last_name='Test',
            user_type='administrator',
            is_staff=True
        )
        admin = Administrator.objects.create(
            user=admin_user,
            role_description='System Administrator'
        )
        
        self.assertEqual(admin_user.email, 'admin@test.com')
        self.assertEqual(admin_user.user_type, 'administrator')
        self.assertTrue(admin_user.is_staff)
        self.assertEqual(admin.role_description, 'System Administrator')

    def test_external_user_creation(self):
        """Test external user creation with all required fields"""
        external_user = User.objects.create_user(
            email='external@test.com',
            username='externaltest',
            password='pass123',
            first_name='External',
            last_name='Test',
            user_type='external'
        )
        external = ExternalUser.objects.create(
            user=external_user,
            organization='Test Company',
            external_user_type='company_supervisor'
        )
        
        self.assertEqual(external_user.email, 'external@test.com')
        self.assertEqual(external_user.user_type, 'external')
        self.assertEqual(external.organization, 'Test Company')
        self.assertEqual(external.external_user_type, 'company_supervisor')

class UserAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create admin user with complete profile
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
        self.client.force_authenticate(user=self.admin_user)

    def test_create_student_api(self):
        """Test student creation through API with all required fields"""
        url = reverse('student-create')
        data = {
            'email': 'newstudent@test.com',
            'username': 'newstudent',
            'password': 'pass123',
            'first_name': 'New',
            'last_name': 'Student',
            'user_type': 'student',
            'matricule': '67890',
            'enrollment_year': 2023,
            'current_year': '4siw',
            'academic_status': 'active'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.count(), 1)
        student = Student.objects.first()
        self.assertEqual(student.matricule, '67890')
        self.assertEqual(student.current_year, '4siw')

    def test_create_teacher_api(self):
        """Test teacher creation through API with all required fields"""
        url = reverse('teacher-create')
        data = {
            'email': 'newteacher@test.com',
            'username': 'newteacher',
            'password': 'pass123',
            'first_name': 'New',
            'last_name': 'Teacher',
            'user_type': 'teacher',
            'department': 'Computer Science',
            'grade': 'maitre_assistant_b'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Teacher.objects.count(), 1)
        teacher = Teacher.objects.first()
        self.assertEqual(teacher.department, 'Computer Science')
        self.assertEqual(teacher.grade, 'maitre_assistant_b')

    def test_user_profile_api(self):
        """Test user profile retrieval and update"""
        # Create a student with complete profile
        student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        student = Student.objects.create(
            user=student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )
        
        # Test profile retrieval
        url = reverse('user-profile', kwargs={'id': student_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'student@test.com')
        self.assertEqual(response.data['profile']['matricule'], '12345')

        # Test profile update
        update_data = {
            'first_name': 'Updated',
            'profile': {
                'current_year': '5siw'
            }
        }
        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_user.refresh_from_db()
        student.refresh_from_db()
        self.assertEqual(student_user.first_name, 'Updated')
        self.assertEqual(student.current_year, '5siw')

    def test_user_list_api(self):
        """Test user listing with filters"""
        # Create users of different types
        student_user = User.objects.create_user(
            email='student@test.com',
            username='studenttest',
            password='pass123',
            first_name='Student',
            last_name='Test',
            user_type='student'
        )
        Student.objects.create(
            user=student_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

        teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            user_type='teacher'
        )
        Teacher.objects.create(
            user=teacher_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )

        # Test filtering by user type
        url = reverse('user-list')
        response = self.client.get(url, {'user_type': 'student'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_type'], 'student')