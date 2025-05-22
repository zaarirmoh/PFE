from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Teacher, Student
from teams.models import Team
from themes.models import Theme, ThemeAssignment
from projects.models import Project, ProjectPhase, Milestone

class ProjectModelTests(TestCase):
    def setUp(self):
        # Create teacher
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Computer Science'
        )

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )

        # Create theme
        self.theme = Theme.objects.create(
            title="Test Theme",
            description="Test theme description",
            academic_year="4siw",
            proposed_by=self.teacher_user
        )

        # Create theme assignment
        self.assignment = ThemeAssignment.objects.create(
            theme=self.theme,
            team=self.team,
            assigned_by=self.teacher_user
        )

        # Create project
        self.project = Project.objects.create(
            title="Test Project",
            description="Test project description",
            theme_assignment=self.assignment,
            status="active"
        )

    def test_project_creation(self):
        """Test project creation and basic attributes"""
        self.assertEqual(self.project.title, "Test Project")
        self.assertEqual(self.project.theme_assignment, self.assignment)
        self.assertEqual(self.project.status, "active")

    def test_project_phases(self):
        """Test project phases management"""
        phase = ProjectPhase.objects.create(
            project=self.project,
            name="Development",
            description="Development phase",
            start_date="2025-05-01",
            end_date="2025-05-30",
            status="in_progress"
        )
        self.assertEqual(self.project.phases.count(), 1)
        self.assertEqual(phase.status, "in_progress")

    def test_project_milestones(self):
        """Test project milestones management"""
        milestone = Milestone.objects.create(
            project=self.project,
            title="MVP Release",
            description="Release MVP version",
            due_date="2025-05-15",
            status="pending"
        )
        self.assertEqual(self.project.milestones.count(), 1)
        self.assertEqual(milestone.status, "pending")

class ProjectAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create teacher
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            username='teachertest',
            password='pass123',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            department='Computer Science'
        )
        
        # Create necessary related objects
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw"
        )
        self.theme = Theme.objects.create(
            title="Test Theme",
            academic_year="4siw",
            proposed_by=self.teacher_user
        )
        self.assignment = ThemeAssignment.objects.create(
            theme=self.theme,
            team=self.team,
            assigned_by=self.teacher_user
        )
        
        self.client.force_authenticate(user=self.teacher_user)

    def test_project_creation_api(self):
        """Test project creation through API"""
        url = reverse('project-list')
        project_data = {
            'title': 'API Test Project',
            'description': 'Project created through API',
            'theme_assignment': self.assignment.id,
            'status': 'active'
        }
        response = self.client.post(url, project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.first().title, 'API Test Project')

    def test_project_phase_creation_api(self):
        """Test creating project phase through API"""
        # First create a project
        project = Project.objects.create(
            title="Test Project",
            theme_assignment=self.assignment,
            status="active"
        )
        
        url = reverse('project-phase-create', kwargs={'project_id': project.id})
        phase_data = {
            'name': 'Implementation',
            'description': 'Implementation phase',
            'start_date': '2025-05-01',
            'end_date': '2025-05-30',
            'status': 'planned'
        }
        response = self.client.post(url, phase_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectPhase.objects.count(), 1)

    def test_project_milestone_creation_api(self):
        """Test creating project milestone through API"""
        project = Project.objects.create(
            title="Test Project",
            theme_assignment=self.assignment,
            status="active"
        )
        
        url = reverse('project-milestone-create', kwargs={'project_id': project.id})
        milestone_data = {
            'title': 'First Deliverable',
            'description': 'Complete first deliverable',
            'due_date': '2025-05-15',
            'status': 'pending'
        }
        response = self.client.post(url, milestone_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Milestone.objects.count(), 1)

    def test_project_status_update_api(self):
        """Test updating project status through API"""
        project = Project.objects.create(
            title="Test Project",
            theme_assignment=self.assignment,
            status="active"
        )
        
        url = reverse('project-detail', kwargs={'pk': project.id})
        update_data = {'status': 'completed'}
        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.status, 'completed')
