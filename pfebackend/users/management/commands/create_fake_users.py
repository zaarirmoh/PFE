import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from users.models import Student, Teacher, Administrator

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate random users for testing purposes'
    
    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=10, help='Number of students to create')
        parser.add_argument('--teachers', type=int, default=10, help='Number of teachers to create')
        parser.add_argument('--admins', type=int, default=3, help='Number of administrators to create')
        parser.add_argument('--password', type=str, default='zaarirmoh', help='Password for all created users')

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        # Get command parameters
        num_students = kwargs.get('students', 10)
        num_teachers = kwargs.get('teachers', 10)
        num_admins = kwargs.get('admins', 3)
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
            
            # Create student profile with valid current_year based on academic_program
            academic_program = random.choice(['preparatory', 'superior'])
            
            # Set current_year according to constraints
            if academic_program == 'preparatory':
                current_year = random.randint(1, 2)
            else:  # superior
                current_year = random.randint(1, 3)
                
            Student.objects.create(
                user=user,
                matricule=f"STU{i+1:04d}",
                enrollment_year=random.randint(2018, 2024),
                academic_program=academic_program,
                current_year=current_year,
                speciality=fake.job() if academic_program == 'superior' else None,
                academic_status=random.choice(['active', 'on_leave', 'graduated'])
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
                user_type='administrator'
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
        
        self.stdout.write(self.style.SUCCESS('Successfully created random users:'))
        self.stdout.write(f'- {num_students} students (password: {password})')
        self.stdout.write(f'- {num_teachers} teachers (password: {password})')
        self.stdout.write(f'- {num_admins} administrators (password: {password})')