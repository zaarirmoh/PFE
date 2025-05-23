from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta

from users.models import User, Student, Teacher
from teams.models import Team, TeamMembership
from themes.models import Theme

fake = Faker()

class Command(BaseCommand):
    help = 'Creates test data for manual testing of auto team assignment service'

    def add_arguments(self, parser):
        parser.add_argument('--academic_year', type=str, default='4siw', help='Academic year to use (e.g., "4siw", "3")')
        parser.add_argument('--students', type=int, default=15, help='Number of students to create')
        parser.add_argument('--teams', type=int, default=3, help='Number of teams to create (some with fewer members than min)')
        parser.add_argument('--themes', type=int, default=5, help='Number of themes to create')
        parser.add_argument('--min_members', type=int, default=3, help='Minimum team members for testing')
        parser.add_argument('--max_members', type=int, default=5, help='Maximum team members for testing')
        
    def handle(self, *args, **options):
        academic_year = options['academic_year']
        num_students = options['students']
        num_teams = options['teams']
        num_themes = options['themes']
        min_members = options['min_members']
        max_members = options['max_members']
        
        self.stdout.write(self.style.SUCCESS(f'Setting up test data for academic year "{academic_year}"'))
        self.stdout.write(f'Creating {num_students} students, {num_teams} teams, and {num_themes} themes')
        self.stdout.write(f'Team size requirements: min={min_members}, max={max_members}')
        
        try:
            with transaction.atomic():
                # Create a teacher user
                teacher = self._create_teacher()
                self.stdout.write(self.style.SUCCESS(f'Created teacher: {teacher.email}, password: test123'))
                
                # Create student users
                students = self._create_students(num_students, academic_year)
                self.stdout.write(self.style.SUCCESS(f'Created {len(students)} students'))
                
                # Create themes
                themes = self._create_themes(num_themes, teacher, academic_year)
                self.stdout.write(self.style.SUCCESS(f'Created {len(themes)} themes'))
                
                # Create teams with varying sizes (including some below min_members)
                teams = self._create_teams(students, academic_year, num_teams, min_members, max_members)
                self.stdout.write(self.style.SUCCESS(f'Created {len(teams)} teams'))
                
                # Summary of the test setup
                self.stdout.write('\n' + '=' * 50)
                self.stdout.write(self.style.SUCCESS('TEST DATA SETUP COMPLETE'))
                self.stdout.write('=' * 50)
                self.stdout.write(f'Academic Year: {academic_year}')
                self.stdout.write(f'Number of students: {len(students)}')
                self.stdout.write(f'Number of teams: {len(teams)}')
                self.stdout.write(f'Team sizes:')
                for team in teams:
                    self.stdout.write(f'  - {team.name}: {team.members.count()} members')
                
                # Calculate how many students don't have teams
                students_with_teams = set()
                for team in teams:
                    for member in team.members.all():
                        students_with_teams.add(member.id)
                
                teamless_count = len(students) - len(students_with_teams)
                self.stdout.write(f'Teamless students: {teamless_count}')
                
                # Instructions for testing
                self.stdout.write('\n' + '=' * 50)
                self.stdout.write(self.style.SUCCESS('MANUAL TESTING INSTRUCTIONS'))
                self.stdout.write('=' * 50)
                self.stdout.write('1. Login to the admin interface with your superuser account')
                self.stdout.write('2. View the created students, teams, and themes')
                self.stdout.write('3. Run the auto team assignment service with:')
                self.stdout.write(f'   python manage.py auto_assign_teams {academic_year} --min_members {min_members} --max_members {max_members}')
                self.stdout.write('   (Add --dry-run to see what would happen without making changes)')
                self.stdout.write('4. Check the admin interface again to see the changes')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test data: {str(e)}'))
            raise
            
    def _create_teacher(self):
        """Create a teacher user"""
        teacher_user = User.objects.create_user(
            email='teacher_test@example.com',
            username='teacher_test',
            password='test123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            user_type='teacher'
        )
        
        Teacher.objects.create(
            user=teacher_user,
            department='Computer Science',
            grade=random.choice(['professeur', 'maitre_conference_a', 'maitre_conference_b', 
                               'maitre_assistant_a', 'maitre_assistant_b'])
        )
        
        return teacher_user
        
    def _create_students(self, count, academic_year):
        """Create student users for the specified academic year"""
        students = []
        
        for i in range(1, count + 1):
            username = f'student_test_{i}'
            email = f'student_test_{i}@example.com'
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
            else:
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password='test123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    user_type='student'
                )
                
                Student.objects.create(
                    user=user,
                    matricule=f'TEST{i:05d}',
                    enrollment_year=timezone.now().year - 3,  # Enrolled 3 years ago
                    current_year=academic_year,
                    academic_status='active'
                )
                
            students.append(user)
            
        return students
        
    def _create_themes(self, count, teacher, academic_year):
        """Create themes proposed by the teacher"""
        themes = []
        
        for i in range(1, count + 1):
            theme = Theme.objects.create(
                title=f'Test Theme {i}: {fake.bs()}',
                description=fake.paragraph(nb_sentences=5),
                proposed_by=teacher,
                tools="Python, Django, ReactJS",
                is_verified=True,
                academic_year=academic_year,
                created_by=teacher,
                updated_by=teacher
            )
            themes.append(theme)
            
        return themes
        
    def _create_teams(self, students, academic_year, count, min_members, max_members):
        """Create teams with varying sizes"""
        teams = []
        students_copy = students.copy()
        random.shuffle(students_copy)  # Randomize student order
        
        # Calculate team sizes: make some undersized, some within range
        available_students = len(students_copy)
        
        # Number of undersized teams (teams with fewer members than min_members)
        undersized_count = min(count // 3, 1)  # At least 1 undersized team, but not more than 1/3 of teams
        normal_count = count - undersized_count
        
        team_sizes = []
        
        # Create undersized teams (1 to min_members-1 members)
        for _ in range(undersized_count):
            if available_students <= 0:
                break
            size = random.randint(1, min_members - 1)
            size = min(size, available_students)
            team_sizes.append(size)
            available_students -= size
            
        # Create normal-sized teams
        for _ in range(normal_count):
            if available_students <= 0:
                break
            size = random.randint(min_members, max_members)
            size = min(size, available_students)
            team_sizes.append(size)
            available_students -= size
            
        # Create the teams
        student_index = 0
        for i, size in enumerate(team_sizes):
            if student_index >= len(students_copy):
                break
                
            team = Team.objects.create(
                name=f'Test Team {i+1}',
                description=f'Created for testing auto team assignment',
                academic_year=academic_year,
                maximum_members=max_members,
            )
            
            # Assign students to this team
            for j in range(size):
                if student_index < len(students_copy):
                    role = TeamMembership.ROLE_OWNER if j == 0 else TeamMembership.ROLE_MEMBER
                    TeamMembership.objects.create(
                        team=team, 
                        user=students_copy[student_index],
                        role=role
                    )
                    student_index += 1
                    
            teams.append(team)
            
        return teams