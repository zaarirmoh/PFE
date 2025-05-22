from django.test import TestCase
from users.models import User, Teacher, Student
from themes.models import Theme
from themes.serializers.theme_creation_serializers import ThemeInputSerializer, ThemeOutputSerializer
from themes.serializers.theme_supervision_serializers import ThemeSupervisionRequestSerializer, CreateThemeSupervisionRequestSerializer, ProcessSupervisionRequestSerializer
from themes.models import ThemeSupervisionRequest
from teams.models import Team, TeamMembership
import json

class ThemeSerializerTests(TestCase):
    """Tests for theme serializers"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
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
        
        # Create co-supervisor
        self.co_teacher_user = User.objects.create_user(
            email='coteacher@test.com',
            username='coteachertest',
            password='pass123',
            first_name='CoTeacher',
            last_name='Test',
            user_type='teacher'
        )
        self.co_teacher = Teacher.objects.create(
            user=self.co_teacher_user,
            department='Computer Science',
            grade='maitre_assistant_a'
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
        
        # Create theme
        self.theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            proposed_by=self.teacher_user,
            academic_year="4siw"
        )
        
        # Add co-supervisor
        self.theme.co_supervisors.add(self.co_teacher_user)
        
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
    
    def test_theme_input_serializer_create(self):
        """Test ThemeInputSerializer for theme creation"""
        data = {
            'title': 'New Theme',
            'description': 'New theme description',
            'academic_year': '4siw',
            'technologies': ['Python', 'Django'],
            'requirements': ['Good programming skills']
        }
        
        # Create context with request containing user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        context = {'request': MockRequest(self.teacher_user)}
        
        # Test serializer validation
        serializer = ThemeInputSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        # Test serializer creation
        theme = serializer.save()
        self.assertEqual(theme.title, 'New Theme')
        self.assertEqual(theme.proposed_by, self.teacher_user)
        self.assertListEqual(list(theme.technologies), ['Python', 'Django'])
        self.assertListEqual(list(theme.requirements), ['Good programming skills'])
    
    def test_theme_input_serializer_update(self):
        """Test ThemeInputSerializer for theme update"""
        data = {
            'title': 'Updated Theme',
            'description': 'Updated theme description',
            'academic_year': '4siw'
        }
        
        # Create context with request containing user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        context = {'request': MockRequest(self.teacher_user)}
        
        # Test serializer validation and update
        serializer = ThemeInputSerializer(instance=self.theme, data=data, context=context, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Update theme
        theme = serializer.save()
        self.assertEqual(theme.title, 'Updated Theme')
        self.assertEqual(theme.description, 'Updated theme description')
    
    def test_theme_output_serializer(self):
        """Test ThemeOutputSerializer"""
        serializer = ThemeOutputSerializer(instance=self.theme)
        data = serializer.data
        
        # Check serialized data
        self.assertEqual(data['title'], 'Test Theme')
        self.assertEqual(data['description'], 'Test theme description')
        self.assertEqual(data['academic_year'], '4siw')
        self.assertEqual(data['proposed_by']['username'], 'teachertest')
        
        # Check co-supervisors
        self.assertEqual(len(data['co_supervisors']), 1)
        self.assertEqual(data['co_supervisors'][0]['username'], 'coteachertest')
    
    def test_create_theme_supervision_request_serializer(self):
        """Test CreateThemeSupervisionRequestSerializer"""
        data = {
            'theme_id': self.theme.id,
            'team_id': self.team.id,
            'message': 'Please supervise our theme'
        }
        
        # Test serializer validation
        serializer = CreateThemeSupervisionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Check validated data
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['theme'], self.theme)
        self.assertEqual(validated_data['team'], self.team)
        self.assertEqual(validated_data['message'], 'Please supervise our theme')
        self.assertEqual(validated_data['invitee'], self.teacher_user)  # Default invitee is theme proposer
    
    def test_process_supervision_request_serializer(self):
        """Test ProcessSupervisionRequestSerializer"""
        # Test accept
        data_accept = {
            'response': 'accept',
            'message': 'I accept this request'
        }
        
        serializer_accept = ProcessSupervisionRequestSerializer(data=data_accept)
        self.assertTrue(serializer_accept.is_valid())
        self.assertEqual(serializer_accept.validated_data['response'], 'accept')
        self.assertEqual(serializer_accept.validated_data['message'], 'I accept this request')
        
        # Test decline
        data_decline = {
            'response': 'decline',
            'message': 'I decline this request'
        }
        
        serializer_decline = ProcessSupervisionRequestSerializer(data=data_decline)
        self.assertTrue(serializer_decline.is_valid())
        self.assertEqual(serializer_decline.validated_data['response'], 'decline')
        self.assertEqual(serializer_decline.validated_data['message'], 'I decline this request')
        
        # Test invalid response
        data_invalid = {
            'response': 'invalid',
            'message': 'Invalid response'
        }
        
        serializer_invalid = ProcessSupervisionRequestSerializer(data=data_invalid)
        self.assertFalse(serializer_invalid.is_valid())
    
    def test_theme_supervision_request_serializer(self):
        """Test ThemeSupervisionRequestSerializer"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING,
            message='Please supervise our theme'
        )
        
        # Serialize the request
        serializer = ThemeSupervisionRequestSerializer(instance=request)
        data = serializer.data
        
        # Check serialized data
        self.assertEqual(data['theme']['id'], self.theme.id)
        self.assertEqual(data['team']['id'], self.team.id)
        self.assertEqual(data['status'], ThemeSupervisionRequest.STATUS_PENDING)
        self.assertEqual(data['message'], 'Please supervise our theme')
        self.assertEqual(data['requester']['id'], self.student_user.id)
        self.assertEqual(data['invitee']['id'], self.teacher_user.id)