from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from teams.models import Team, TeamMembership
from timelines.models import Timeline, Phase, Event, EventCategory
from datetime import datetime, timedelta

class TimelineTests(TestCase):
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

        # Create timeline
        self.timeline = Timeline.objects.create(
            title="Project Timeline",
            description="Project development timeline",
            team=self.team,
            created_by=self.teacher_user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=90)
        )

    def test_timeline_creation(self):
        """Test timeline creation and basic attributes"""
        self.assertEqual(self.timeline.title, "Project Timeline")
        self.assertEqual(self.timeline.team, self.team)
        self.assertEqual(self.timeline.created_by, self.teacher_user)

    def test_phase_creation(self):
        """Test creating phases in timeline"""
        phase = Phase.objects.create(
            timeline=self.timeline,
            name="Development Phase",
            description="Main development phase",
            start_date=self.timeline.start_date,
            end_date=self.timeline.start_date + timedelta(days=30),
            order=1
        )
        self.assertEqual(phase.timeline, self.timeline)
        self.assertEqual(phase.order, 1)

class EventTests(TestCase):
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

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )

        # Create timeline
        self.timeline = Timeline.objects.create(
            title="Project Timeline",
            team=self.team,
            created_by=self.teacher_user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=90)
        )

        # Create phase
        self.phase = Phase.objects.create(
            timeline=self.timeline,
            name="Development",
            start_date=self.timeline.start_date,
            end_date=self.timeline.start_date + timedelta(days=30),
            order=1
        )

        # Create event category
        self.category = EventCategory.objects.create(
            name="Milestone",
            description="Project milestone events"
        )

    def test_event_creation(self):
        """Test creating events in a phase"""
        event = Event.objects.create(
            phase=self.phase,
            category=self.category,
            title="Code Review",
            description="Team code review session",
            date=self.phase.start_date + timedelta(days=7),
            created_by=self.teacher_user
        )
        self.assertEqual(event.phase, self.phase)
        self.assertEqual(event.category, self.category)
        self.assertEqual(event.created_by, self.teacher_user)

class TimelineAPITests(APITestCase):
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

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )

        self.client.force_authenticate(user=self.teacher_user)

        # Timeline data for API tests
        self.timeline_data = {
            'title': 'API Timeline',
            'description': 'Timeline created through API',
            'team': self.team.id,
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=90)).isoformat()
        }

    def test_timeline_creation_api(self):
        """Test timeline creation through API"""
        url = reverse('timeline-create')
        response = self.client.post(url, self.timeline_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Timeline.objects.count(), 1)
        self.assertEqual(Timeline.objects.first().title, 'API Timeline')

    def test_phase_creation_api(self):
        """Test phase creation through API"""
        # First create a timeline
        timeline = Timeline.objects.create(
            title="Test Timeline",
            team=self.team,
            created_by=self.teacher_user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=90)
        )

        url = reverse('phase-create')
        phase_data = {
            'timeline': timeline.id,
            'name': 'API Phase',
            'description': 'Phase created through API',
            'start_date': timeline.start_date.isoformat(),
            'end_date': (timeline.start_date + timedelta(days=30)).isoformat(),
            'order': 1
        }
        response = self.client.post(url, phase_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Phase.objects.count(), 1)

    def test_event_creation_api(self):
        """Test event creation through API"""
        # Create timeline and phase first
        timeline = Timeline.objects.create(
            title="Test Timeline",
            team=self.team,
            created_by=self.teacher_user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=90)
        )
        phase = Phase.objects.create(
            timeline=timeline,
            name="Test Phase",
            start_date=timeline.start_date,
            end_date=timeline.start_date + timedelta(days=30),
            order=1
        )
        category = EventCategory.objects.create(
            name="Test Category"
        )

        url = reverse('event-create')
        event_data = {
            'phase': phase.id,
            'category': category.id,
            'title': 'API Event',
            'description': 'Event created through API',
            'date': (phase.start_date + timedelta(days=7)).isoformat()
        }
        response = self.client.post(url, event_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)