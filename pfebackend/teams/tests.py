from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Student, Teacher
from teams.models import Team, TeamMembership, TeamInvitation, TeamJoinRequest
from teams.serializers import TeamSerializer
from django.utils import timezone

class TeamTests(TestCase):
    def setUp(self):
        # Create supervisor (teacher) with complete profile
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

        # Create team members (students) with complete profiles
        self.student1_user = User.objects.create_user(
            email='student1@test.com',
            username='student1test',
            password='pass123',
            first_name='Student1',
            last_name='Test',
            user_type='student'
        )
        self.student1 = Student.objects.create(
            user=self.student1_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

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

        # Create team
        self.team = Team.objects.create(
            name="Test Team",
            academic_year="4siw",
            supervisor=self.teacher_user
        )

        # Add team members
        TeamMembership.objects.create(
            team=self.team,
            user=self.student1_user,
            role=TeamMembership.ROLE_LEADER
        )
        TeamMembership.objects.create(
            team=self.team,
            user=self.student2_user,
            role=TeamMembership.ROLE_MEMBER
        )

    def test_team_creation(self):
        """Test team creation and basic attributes"""
        self.assertEqual(self.team.name, "Test Team")
        self.assertEqual(self.team.academic_year, "4siw")
        self.assertEqual(self.team.supervisor, self.teacher_user)
        self.assertEqual(self.team.members.count(), 2)

    def test_team_leader(self):
        """Test team leader assignment and retrieval"""
        leader_membership = TeamMembership.objects.get(team=self.team, role=TeamMembership.ROLE_LEADER)
        self.assertEqual(leader_membership.user, self.student1_user)

    def test_team_member_roles(self):
        """Test team member role assignments"""
        member_membership = TeamMembership.objects.get(team=self.team, user=self.student2_user)
        self.assertEqual(member_membership.role, TeamMembership.ROLE_MEMBER)

class TeamAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create supervisor (teacher) with complete profile
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

        # Create students with complete profiles
        self.student1_user = User.objects.create_user(
            email='student1@test.com',
            username='student1test',
            password='pass123',
            first_name='Student1',
            last_name='Test',
            user_type='student'
        )
        self.student1 = Student.objects.create(
            user=self.student1_user,
            matricule='12345',
            enrollment_year=2023,
            current_year='4siw',
            academic_status='active'
        )

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

        self.client.force_authenticate(user=self.teacher_user)

    def test_create_team_api(self):
        """Test team creation through API"""
        url = reverse('team-create')
        data = {
            'name': 'API Test Team',
            'academic_year': '4siw',
            'supervisor': self.teacher_user.id,
            'members': [
                {'user': self.student1_user.id, 'role': TeamMembership.ROLE_LEADER},
                {'user': self.student2_user.id, 'role': TeamMembership.ROLE_MEMBER}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.count(), 1)
        team = Team.objects.first()
        self.assertEqual(team.name, 'API Test Team')
        self.assertEqual(team.members.count(), 2)

    def test_team_list_api(self):
        """Test team listing endpoint"""
        # Create some teams first
        team1 = Team.objects.create(
            name="Team 1",
            academic_year="4siw",
            supervisor=self.teacher_user
        )
        TeamMembership.objects.create(
            team=team1,
            user=self.student1_user,
            role=TeamMembership.ROLE_LEADER
        )

        team2 = Team.objects.create(
            name="Team 2",
            academic_year="4siw",
            supervisor=self.teacher_user
        )
        TeamMembership.objects.create(
            team=team2,
            user=self.student2_user,
            role=TeamMembership.ROLE_LEADER
        )

        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_team_detail_api(self):
        """Test team detail retrieval"""
        team = Team.objects.create(
            name="Test Team",
            academic_year="4siw",
            supervisor=self.teacher_user
        )
        TeamMembership.objects.create(
            team=team,
            user=self.student1_user,
            role=TeamMembership.ROLE_LEADER
        )

        url = reverse('team-detail', kwargs={'pk': team.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Team')
        self.assertEqual(len(response.data['members']), 1)

    def test_update_team_members_api(self):
        """Test updating team members through API"""
        team = Team.objects.create(
            name="Test Team",
            academic_year="4siw",
            supervisor=self.teacher_user
        )
        TeamMembership.objects.create(
            team=team,
            user=self.student1_user,
            role=TeamMembership.ROLE_LEADER
        )

        url = reverse('team-update-members', kwargs={'pk': team.pk})
        data = {
            'members': [
                {'user': self.student1_user.id, 'role': TeamMembership.ROLE_MEMBER},
                {'user': self.student2_user.id, 'role': TeamMembership.ROLE_LEADER}
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(team.members.count(), 2)
        new_leader = TeamMembership.objects.get(team=team, role=TeamMembership.ROLE_LEADER)
        self.assertEqual(new_leader.user, self.student2_user)