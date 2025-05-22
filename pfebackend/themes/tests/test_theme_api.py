from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from themes.models import Theme, ThemeSupervisionRequest
from themes.models.project_models import ThemeAssignment
from teams.models import Team, TeamMembership
import json

class ThemeAPITests(APITestCase):
    """Tests for theme API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create teacher user
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

        # Create student user
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
        
        # Create team for the student
        self.team = Team.objects.create(
            name="Test Team",
            description="Test team description",
            academic_year="4siw",
            maximum_members=3
        )
        
        # Add student as team owner
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_OWNER
        )

        # Authenticate as teacher by default
        self.client.force_authenticate(user=self.teacher_user)
        
        # Create theme
        self.theme = Theme.objects.create(
            title="API Test Theme",
            description="Theme for API testing",
            proposed_by=self.teacher_user,
            academic_year="4siw"
        )
    
    def test_theme_list(self):
        """Test listing themes"""
        url = reverse('theme-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination
        self.assertTrue('results' in response.data)
        self.assertEqual(len(response.data['results']), 1)  
        self.assertEqual(response.data['results'][0]['title'], 'API Test Theme')
    
    def test_theme_create(self):
        """Test creating a theme"""
        url = reverse('theme-list')
        data = {
            'title': 'New API Theme',
            'description': 'Theme created through API test',
            'academic_year': '4siw',
            'technologies': ['Python', 'Django'],
            'requirements': ['Good programming skills']
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Theme.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New API Theme')
        self.assertEqual(response.data['proposed_by']['username'], 'teachertest')
    
    def test_theme_retrieve(self):
        """Test retrieving a theme"""
        url = reverse('theme-detail', args=[self.theme.id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'API Test Theme')
    
    def test_theme_update(self):
        """Test updating a theme"""
        url = reverse('theme-detail', args=[self.theme.id])
        data = {
            'title': 'Updated API Theme',
            'description': 'Updated theme description',
            'academic_year': '4siw',
        }
        
        response = self.client.patch(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated API Theme')
        
        # Refresh from database
        self.theme.refresh_from_db()
        self.assertEqual(self.theme.title, 'Updated API Theme')
    
    def test_theme_delete(self):
        """Test deleting a theme"""
        url = reverse('theme-detail', args=[self.theme.id])
        response = self.client.delete(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Theme.objects.count(), 0)
    
    def test_student_cannot_create_theme(self):
        """Test that students cannot create themes"""
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('theme-list')
        data = {
            'title': 'Student Theme',
            'description': 'Theme created by student',
            'academic_year': '4siw',
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response (should fail with 403 Forbidden)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_theme_filter_by_academic_year(self):
        """Test filtering themes by academic year"""
        # Create another theme with different academic year
        Theme.objects.create(
            title="Another Theme",
            description="Another theme for testing",
            proposed_by=self.teacher_user,
            academic_year="3siw"
        )
        
        # Test filter
        url = reverse('theme-list') + "?academic_year=4siw"
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'API Test Theme')
    
    def test_theme_filter_by_proposed_by(self):
        """Test filtering themes by proposer"""
        # Create another teacher
        another_teacher = User.objects.create_user(
            email='another@test.com',
            username='anotherteacher',
            password='pass123',
            user_type='teacher'
        )
        Teacher.objects.create(
            user=another_teacher,
            department='Computer Science',
            grade='maitre_assistant_b'
        )
        
        # Create theme proposed by the other teacher
        Theme.objects.create(
            title="Another Theme",
            description="Another theme for testing",
            proposed_by=another_teacher,
            academic_year="4siw"
        )
        
        # Test filter
        url = reverse('theme-list') + f"?proposed_by={self.teacher_user.id}"
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'API Test Theme')
    
    def test_theme_search(self):
        """Test searching themes by title or description"""
        # Create themes with different titles/descriptions
        Theme.objects.create(
            title="AI Project Theme",
            description="Theme about artificial intelligence",
            proposed_by=self.teacher_user,
            academic_year="4siw"
        )
        
        # Test search
        url = reverse('theme-list') + "?search=AI"
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'AI Project Theme')


class ThemeSupervisionAPITests(APITestCase):
    """Tests for theme supervision API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create teacher
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
        
        # Create student
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
            description="Test team description",
            academic_year="4siw",
            maximum_members=3
        )
        
        # Add student as team owner
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_OWNER
        )
        
        # Create theme
        self.theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            proposed_by=self.teacher_user,
            academic_year="4siw"
        )
    
    def test_create_supervision_request_api(self):
        """Test creating a theme supervision request via API"""
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('create-supervision-request')
        data = {
            'theme_id': self.theme.id,
            'team_id': self.team.id,
            'message': 'Please supervise our theme'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('supervision_request' in response.data)
        self.assertEqual(response.data['supervision_request']['theme']['id'], self.theme.id)
        self.assertEqual(response.data['supervision_request']['team']['id'], self.team.id)
        self.assertEqual(response.data['supervision_request']['status'], ThemeSupervisionRequest.STATUS_PENDING)
        
        # Check that a request was created
        self.assertEqual(ThemeSupervisionRequest.objects.count(), 1)
        request = ThemeSupervisionRequest.objects.first()
        self.assertEqual(request.theme, self.theme)
        self.assertEqual(request.team, self.team)
        self.assertEqual(request.requester, self.student_user)
    
    def test_get_team_supervision_requests_api(self):
        """Test getting supervision requests for a team via API"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('team-supervision-requests', args=[self.team.id])
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['theme']['id'], self.theme.id)
        self.assertEqual(response.data[0]['status'], ThemeSupervisionRequest.STATUS_PENDING)
    
    def test_get_user_supervision_requests_api(self):
        """Test getting supervision requests for a user via API"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Authenticate as teacher
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('user-supervision-requests')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['theme']['id'], self.theme.id)
        self.assertEqual(response.data[0]['status'], ThemeSupervisionRequest.STATUS_PENDING)
    
    def test_respond_to_supervision_request_api(self):
        """Test responding to a supervision request via API"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Authenticate as teacher
        self.client.force_authenticate(user=self.teacher_user)
        
        url = reverse('supervision-request-response', args=[request.id])
        
        # Accept the request
        data = {
            'response': 'accept',
            'message': 'I accept this request'
        }
        
        response = self.client.patch(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was accepted
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_ACCEPTED)
        self.assertEqual(request.response_message, 'I accept this request')
        
        # Check that a theme assignment was created
        self.assertTrue(ThemeAssignment.objects.filter(theme=self.theme, team=self.team).exists())
    
    def test_cancel_supervision_request_api(self):
        """Test cancelling a supervision request via API"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)
        
        url = reverse('cancel-supervision-request', args=[request.id])
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was cancelled
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_CANCELLED)