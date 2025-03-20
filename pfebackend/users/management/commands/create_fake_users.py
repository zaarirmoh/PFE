import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from users.models import Student, Teacher, Administrator

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate random users for testing purposes'

    def handle(self, *args, **kwargs):
        fake = Faker()
        password = 'zaarirmoh'
        
        self.stdout.write('Creating random users...')
        
        # Create 10 students
        self.stdout.write('Creating students...')
        for i in range(10):
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
            
            # Create student profile
            academic_program = random.choice(['preparatory', 'superior'])
            current_year = random.randint(1, 5)
            Student.objects.create(
                user=user,
                matricule=f"STU{i+1:04d}",
                enrollment_year=random.randint(2018, 2024),
                academic_program=academic_program,
                current_year=current_year,
                speciality=fake.job() if academic_program == 'superior' else None,
                academic_status=random.choice(['active'])
            )
        
        # Create 10 teachers
        self.stdout.write('Creating teachers...')
        for i in range(10):
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
        
        # Create 3 administrators
        self.stdout.write('Creating administrators...')
        for i in range(3):
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
        self.stdout.write(f'- 10 students (password: {password})')
        self.stdout.write(f'- 10 teachers (password: {password})')
        self.stdout.write(f'- 3 administrators (password: {password})')