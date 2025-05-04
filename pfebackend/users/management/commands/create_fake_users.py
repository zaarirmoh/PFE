import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from users.models import Student, Teacher, Administrator, StudentSkill, ExternalUser

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate random users for testing purposes'
    
    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=10, help='Number of students to create')
        parser.add_argument('--teachers', type=int, default=10, help='Number of teachers to create')
        parser.add_argument('--admins', type=int, default=3, help='Number of administrators to create')
        parser.add_argument('--externals', type=int, default=5, help='Number of external users to create')
        parser.add_argument('--password', type=str, default='zaarirmoh', help='Password for all created users')

    def handle(self, **kwargs):
        fake = Faker()
        
        # Get command parameters
        num_students = kwargs.get('students', 10)
        num_teachers = kwargs.get('teachers', 10)
        num_admins = kwargs.get('admins', 3)
        num_externals = kwargs.get('externals', 5)
        password = kwargs.get('password', 'zaarirmoh')
        
        self.stdout.write('Creating random users...')
        
        # Create students
        self.stdout.write(f'Creating {num_students} students...')
        for i in range(num_students):
            # Create user
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"student{i+1}@example.com"
            username = f"student{i+1}"
            
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                user_type='student'
            )
            
            # Choose a random academic year based on the ACADEMIC_YEAR_CHOICES
            academic_year_choices = [
                '2', '3', '4siw', '4isi', '4iasd', '5siw', '5isi', '5iasd'
            ]
            
            # Create student profile with valid current_year
            student = Student.objects.create(
                user=user,
                matricule=f"STU{i+1:04d}",
                enrollment_year=random.randint(2018, 2024),
                current_year=random.choice(academic_year_choices),
                # group=random.randint(1, 6),
                academic_status=random.choice(['active'])
            )
            
            # Add some random skills for each student
            available_skills = [
                "Python", "Java", "JavaScript", "HTML/CSS", "React", 
                "Django", "SQL", "Data Analysis", "Machine Learning",
                "UI/UX Design", "Project Management", "Network Security"
            ]
            
            # Add 1-4 random skills for each student
            num_skills = random.randint(1, 4)
            for _ in range(num_skills):
                skill_name = random.choice(available_skills)
                proficiency = random.choice(['beginner', 'intermediate', 'advanced', 'expert'])
                
                # Create the skill if it doesn't already exist for this student
                StudentSkill.objects.get_or_create(
                    student=student,
                    name=skill_name,
                    defaults={'proficiency_level': proficiency}
                )
        
        # Create teachers
        self.stdout.write(f'Creating {num_teachers} teachers...')
        for i in range(num_teachers):
            # Create user
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"teacher{i+1}@example.com"
            username = f"teacher{i+1}"
            
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                user_type='teacher'
            )
            
            # Create teacher profile
            Teacher.objects.create(
                user=user,
                department=random.choice(['Computer Science', 'Mathematics', 'Physics', 'Chemistry', 'Biology']),
                grade=random.choice([
                    'professeur',
                    'maitre_conferences_a',
                    'maitre_conferences_b',
                    'maitre_assistant_a',
                    'maitre_assistant_b'
                ])
            )
        
        # Create administrators
        self.stdout.write(f'Creating {num_admins} administrators...')
        for i in range(num_admins):
            # Create user
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"admin{i+1}@example.com"
            username = f"admin{i+1}"
            
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                user_type='administrator',
                is_staff=True
            )
            
            # Create administrator profile
            Administrator.objects.create(
                user=user,
                role_description=random.choice([
                    'System Administrator',
                    'Academic Affairs',
                    'Student Affairs',
                    'Technical Support',
                    'Department Head'
                ])
            )
            
        # Create external users
        self.stdout.write(f'Creating {num_externals} external users...')
        for i in range(num_externals):
            # Create user
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"external{i+1}@example.com"
            username = f"external{i+1}"
            
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                user_type='external'
            )
            
            # Create external user profile
            ExternalUser.objects.create(
                user=user,
                EXTERNAL_USER_TYPE=random.choice([
                    ExternalUser.UNIVERSITY,
                    ExternalUser.COMPANY,
                    ExternalUser.OTHER
                ])
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully created random users:'))
        self.stdout.write(f'- {num_students} students (password: {password})')
        self.stdout.write(f'- {num_teachers} teachers (password: {password})')
        self.stdout.write(f'- {num_admins} administrators (password: {password})')
        self.stdout.write(f'- {num_externals} external users (password: {password})')