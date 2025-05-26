from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from teams.models import Team, TeamMembership
from supervision.models import Meeting, Upload, ResourceComment, Defense, JuryMember
from datetime import datetime, timedelta

class MeetingTests(TestCase):
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

        # Create meeting
        self.meeting = Meeting.objects.create(
            title="Progress Meeting",
            description="Weekly progress review",
            team=self.team,
            scheduled_by=self.teacher_user,
            scheduled_at=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            location_type='online',
            meeting_link='https://meet.example.com'
        )

    def test_meeting_creation(self):
        """Test meeting creation and basic attributes"""
        self.assertEqual(self.meeting.title, "Progress Meeting")
        self.assertEqual(self.meeting.team, self.team)
        self.assertEqual(self.meeting.scheduled_by, self.teacher_user)
        self.assertEqual(self.meeting.duration_minutes, 60)

    def test_meeting_scheduling(self):
        """Test meeting scheduling functionality"""
        scheduled_time = timezone.now() + timedelta(days=1)
        meeting = Meeting.objects.create(
            title="Another Meeting",
            team=self.team,
            scheduled_by=self.teacher_user,
            scheduled_at=scheduled_time,
            duration_minutes=30
        )
        self.assertEqual(meeting.status, 'scheduled')
        self.assertEqual(meeting.duration_minutes, 30)

class UploadTests(TestCase):
    def setUp(self):
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

        # Create upload
        self.upload = Upload.objects.create(
            title="Project Documentation",
            description="Initial project documentation",
            team=self.team,
            uploaded_by=self.student_user,
            file_url="https://example.com/doc.pdf"
        )

    def test_upload_creation(self):
        """Test upload creation and basic attributes"""
        self.assertEqual(self.upload.title, "Project Documentation")
        self.assertEqual(self.upload.team, self.team)
        self.assertEqual(self.upload.uploaded_by, self.student_user)

    def test_upload_commenting(self):
        """Test commenting on uploads"""
        comment = ResourceComment.objects.create(
            upload=self.upload,
            author=self.student_user,
            content="Great documentation!"
        )
        self.assertEqual(comment.content, "Great documentation!")
        self.assertEqual(comment.author, self.student_user)

class DefenseTests(TestCase):
    def setUp(self):
        # Create jury president with complete profile
        self.president_user = User.objects.create_user(
            email='president@test.com',
            username='president',
            password='pass123',
            first_name='Jury',
            last_name='President',
            user_type='teacher'
        )
        self.president = Teacher.objects.create(
            user=self.president_user,
            department='Computer Science',
            grade='professeur'
        )

        # Create supervisor with complete profile
        self.supervisor_user = User.objects.create_user(
            email='supervisor@test.com',
            username='supervisor',
            password='pass123',
            first_name='Project',
            last_name='Supervisor',
            user_type='teacher'
        )
        self.supervisor = Teacher.objects.create(
            user=self.supervisor_user,
            department='Computer Science',
            grade='maitre_assistant_b'
        )

        # Create student with complete profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            username='student',
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

        # Create defense
        self.defense = Defense.objects.create(
            title="Final Project Defense",
            team=self.team,
            date=timezone.now().date() + timedelta(days=7),
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room A101'
        )

        

    def test_defense_creation(self):
        """Test defense creation and basic attributes"""
        self.assertEqual(self.defense.title, "Final Project Defense")
        self.assertEqual(self.defense.team, self.team)
        self.assertEqual(self.defense.location, "Room A101")

    def test_jury_assignment(self):
        """Test assigning jury members to defense"""
        # Assign president
        president_member = JuryMember.objects.create(
            defense=self.defense,
            user=self.president_user,
            role=self.president_role,
            is_president=True
        )
        
        # Assign supervisor
        supervisor_member = JuryMember.objects.create(
            defense=self.defense,
            user=self.supervisor_user,
            role=self.supervisor_role,
            is_president=False
        )

        self.assertEqual(self.defense.jury_members.count(), 2)
        self.assertTrue(president_member.is_president)
        self.assertFalse(supervisor_member.is_president)

class SupervisionAPITests(APITestCase):
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

        self.client.force_authenticate(user=self.teacher_user)

    def test_schedule_meeting_api(self):
        """Test scheduling a meeting through API"""
        url = reverse('meeting-create')
        meeting_data = {
            'title': 'API Test Meeting',
            'description': 'Meeting scheduled through API',
            'team': self.team.id,
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'duration_minutes': 60,
            'location_type': 'online',
            'meeting_link': 'https://meet.test.com'
        }
        response = self.client.post(url, meeting_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meeting.objects.count(), 1)

    def test_create_defense_api(self):
        """Test creating a defense through API"""
        url = reverse('defense-create')
        defense_data = {
            'title': 'API Test Defense',
            'team': self.team.id,
            'date': (timezone.now().date() + timedelta(days=7)).isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'location': 'Room B102'
        }
        response = self.client.post(url, defense_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Defense.objects.count(), 1)