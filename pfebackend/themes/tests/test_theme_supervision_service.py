from django.test import TestCase
from django.utils import timezone
from users.models import User, Teacher, Student
from themes.models import Theme, ThemeSupervisionRequest
from themes.models.project_models import ThemeAssignment
from teams.models import Team, TeamMembership
from themes.services.theme_supervision_service import ThemeSupervisionService
from django.core.exceptions import ValidationError

class ThemeSupervisionServiceTests(TestCase):
    """Tests for theme supervision service"""
    
    def setUp(self):
        """Set up test data"""
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
        
        # Create co-supervisor teacher
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

        # Create student user (team owner)
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
        
        # Create a second student (team member)
        self.student2_user = User.objects.create_user(
            email='student2@test.com',
            username='student2test',
            password='pass123',
            first_name='Student2',
            last_name='Test',
            user_type='student'
        )
        self.student2 = Student.objects.create(
            user=self.student2_user,
            matricule='67890',
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
        
        # Create team with students
        self.team = Team.objects.create(
            name="Test Team",
            description="Test team description",
            academic_year="4siw",
            maximum_members=3
        )
        
        # Add team owner
        TeamMembership.objects.create(
            team=self.team,
            user=self.student_user,
            role=TeamMembership.ROLE_OWNER
        )
        
        # Add team member
        TeamMembership.objects.create(
            team=self.team,
            user=self.student2_user,
            role=TeamMembership.ROLE_MEMBER
        )

    def test_create_supervision_request(self):
        """Test creating a supervision request"""
        # Create a supervision request
        request = ThemeSupervisionService.create_supervision_request(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            message="Please supervise our theme"
        )
        
        # Check that the request was created correctly
        self.assertEqual(request.theme, self.theme)
        self.assertEqual(request.team, self.team)
        self.assertEqual(request.requester, self.student_user)
        self.assertEqual(request.invitee, self.teacher_user)
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_PENDING)
        self.assertEqual(request.message, "Please supervise our theme")
    
    def test_process_supervision_request_accept(self):
        """Test accepting a supervision request"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING,
            message="Please supervise our theme"
        )
        
        # Accept the request
        success, result = ThemeSupervisionService.process_supervision_request_response(
            user=self.teacher_user,
            request_id=request.id,
            response="accept",
            message="I'll be happy to supervise"
        )
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was accepted
        self.assertTrue(success)
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_ACCEPTED)
        self.assertEqual(request.response_message, "I'll be happy to supervise")
        
        # Check that a theme assignment was created
        self.assertTrue(ThemeAssignment.objects.filter(theme=self.theme, team=self.team).exists())
    
    def test_process_supervision_request_decline(self):
        """Test declining a supervision request"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING,
            message="Please supervise our theme"
        )
        
        # Decline the request
        success, result = ThemeSupervisionService.process_supervision_request_response(
            user=self.teacher_user,
            request_id=request.id,
            response="decline",
            message="I'm too busy right now"
        )
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was declined
        self.assertTrue(success)
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_DECLINED)
        self.assertEqual(request.response_message, "I'm too busy right now")
        
        # Check that no theme assignment was created
        self.assertFalse(ThemeAssignment.objects.filter(theme=self.theme, team=self.team).exists())

    def test_get_user_pending_supervision_requests(self):
        """Test getting pending supervision requests for a user"""
        # Create some supervision requests
        request1 = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Get pending requests for teacher
        requests = ThemeSupervisionService.get_user_pending_supervision_requests(self.teacher_user)
        
        # Check that the request was returned
        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests.first(), request1)
        
        # Check co-supervisor requests
        co_requests = ThemeSupervisionService.get_user_pending_supervision_requests(self.co_teacher_user)
        self.assertEqual(co_requests.count(), 1)
        
        # Accept the request
        request1.status = ThemeSupervisionRequest.STATUS_ACCEPTED
        request1.save()
        
        # Check that no pending requests are returned
        requests = ThemeSupervisionService.get_user_pending_supervision_requests(self.teacher_user)
        self.assertEqual(requests.count(), 0)
    
    def test_get_team_supervision_requests(self):
        """Test getting supervision requests for a team"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Get requests for team
        requests = ThemeSupervisionService.get_team_supervision_requests(self.team)
        
        # Check that the request was returned
        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests.first(), request)
    
    def test_cancel_supervision_request(self):
        """Test cancelling a supervision request"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Cancel the request
        success = ThemeSupervisionService.cancel_supervision_request(
            request_id=request.id,
            user=self.student_user
        )
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was cancelled
        self.assertTrue(success)
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_CANCELLED)
    
    def test_unauthorized_cancel_supervision_request(self):
        """Test that only team owners can cancel supervision requests"""
        # Create a supervision request
        request = ThemeSupervisionRequest.objects.create(
            theme=self.theme,
            team=self.team,
            requester=self.student_user,
            invitee=self.teacher_user,
            status=ThemeSupervisionRequest.STATUS_PENDING
        )
        
        # Attempt to cancel the request as a non-owner
        success = ThemeSupervisionService.cancel_supervision_request(
            request_id=request.id,
            user=self.student2_user  # Not the team owner
        )
        
        # Refresh the request from the database
        request.refresh_from_db()
        
        # Check that the request was not cancelled
        self.assertFalse(success)
        self.assertEqual(request.status, ThemeSupervisionRequest.STATUS_PENDING)