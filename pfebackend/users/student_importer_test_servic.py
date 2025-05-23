import pandas as pd
from users.models import User, Student
from django.db import transaction
from datetime import datetime

# Helper mapping of academic year transitions
ACADEMIC_YEAR_TRANSITIONS = {
    '2': '3',
    '3': '4siw',
    '4siw': '5siw',
    '4isi': '5isi',
    '4iasd': '5iasd',
}

def import_students_from_excel(file_path: str, academic_year: str):
    """
    Imports or updates student data from an Excel file.
    
    Only students marked 'Admis(e)' are promoted to the next academic year.
    """
    df = pd.read_excel(file_path,skiprows=6)
    
    required_columns = ['N° d\'inscription', 'Nom', 'Prénom', 'Décision']
    # if not all(col in df.columns for col in required_columns):
    #     raise ValueError("Missing required columns in Excel file.")

    with transaction.atomic():
        for _, row in df.iterrows():
            matricule = str(row['N° d\'inscription']).strip()
            nom = str(row['Nom']).strip().capitalize()
            prenom = str(row['Prénom']).strip().capitalize()
            decision = str(row['Décision']).strip().lower()

            try:
                student = Student.objects.select_related('user').get(
                    matricule=matricule, current_year=academic_year
                )
            except Student.DoesNotExist:
                print(f"Student with matricule {matricule} not found for year {academic_year}. Skipping.")
                continue

            if "admis" in decision:
                next_year = ACADEMIC_YEAR_TRANSITIONS.get(academic_year)
                if next_year:
                    student.current_year = next_year
                    student.save()
                    print(f"Promoted {student.get_full_name()} to {next_year}.")
                else:
                    print(f"No transition mapping defined for year '{academic_year}'. Skipping {student.get_full_name()}.")
            else:
                print(f"{student.get_full_name()} is marked '{decision}', not promoted.")




from django.utils.text import slugify
import pandas as pd
from django.utils.text import slugify
from django.db import transaction

def create_students_from_excel(file_path: str, academic_year: str):
    print("Creating students from Excel file...")
    """
    Creates new student users from an Excel file and assigns them to the given academic year.
    Starts reading from row 7 (zero-based index 6), and skips students with existing records.
    """
    df = pd.read_excel(file_path, skiprows=6)
    print(df.columns)
    required_columns = ['N° d\'inscription', 'Nom', 'Prénom']
    actual_columns = [col.strip().lower() for col in df.columns]

    required_normalized = [col.strip().lower() for col in required_columns]

    if not all(col in actual_columns for col in required_normalized):
        print("Columns found:", df.columns)
        raise ValueError("Missing required columns in Excel file.")


    created_count = 0
    skipped_count = 0

    with transaction.atomic():
        for _, row in df.iterrows():
            matricule = str(row["N° d'inscription"]).strip()
            last_name = str(row['Nom']).strip().capitalize()
            first_name = str(row['Prénom']).strip().capitalize()

            if not matricule or not first_name or not last_name:
                print(f"Skipping student with missing data: {matricule}, {first_name}, {last_name}")
                skipped_count += 1
                continue

            if Student.objects.filter(matricule=matricule).exists():
                print(f"Student with matricule {matricule} already exists. Skipping.")
                skipped_count += 1
                continue

            # Generate unique username/email
            base_username = slugify(f"{first_name}.{last_name}")
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            email = f"{username}@esi-sba.dz"

            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password='zaarirmoh',  # Consider replacing this with a random or temporary password
                user_type='student'
            )

            Student.objects.create(
                user=user,
                matricule=matricule,
                # enrollment_year=enrollment_year,
                current_year=academic_year,
                academic_status='active'
            )

            print(f"Created student {user.get_full_name()} with matricule {matricule}")
            created_count += 1

    print(f"Import complete. Created: {created_count}, Skipped: {skipped_count}")

# def create_students_from_excel(file_path: str, academic_year: str, enrollment_year: int):
#     """
#     Creates new student users from an Excel file and assigns them to the given academic year.
#     Skips students with an existing user or student record using the matricule.
#     """
#     df = pd.read_excel(file_path)

#     required_columns = ['N° d\'inscription', 'Nom', 'Prénom']
#     if not all(col in df.columns for col in required_columns):
#         raise ValueError("Missing required columns in Excel file.")

#     created_count = 0
#     skipped_count = 0

#     with transaction.atomic():
#         for _, row in df.iterrows():
#             matricule = str(row['N° d\'inscription']).strip()
#             last_name = str(row['Nom']).strip().capitalize()
#             first_name = str(row['Prénom']).strip().capitalize()

#             if not matricule or not first_name or not last_name:
#                 print(f"Skipping student with missing data: {matricule}, {first_name}, {last_name}")
#                 skipped_count += 1
#                 continue

#             if Student.objects.filter(matricule=matricule).exists():
#                 print(f"Student with matricule {matricule} already exists. Skipping.")
#                 skipped_count += 1
#                 continue

#             # Generate a unique email/username
#             base_username = slugify(f"{first_name}.{last_name}")
#             username = base_username
#             counter = 1
#             while User.objects.filter(username=username).exists():
#                 username = f"{base_username}{counter}"
#                 counter += 1

#             email = f"{username}@esi-sba.dz"

#             user = User.objects.create_user(
#                 email=email,
#                 username=username,
#                 first_name=first_name,
#                 last_name=last_name,
#                 password='zaarirmoh',  # You should change this or force reset
#                 user_type='student'
#             )

#             Student.objects.create(
#                 user=user,
#                 matricule=matricule,
#                 enrollment_year=enrollment_year,
#                 current_year=academic_year,
#                 academic_status='active'
#             )

#             print(f"Created student {user.get_full_name()} with matricule {matricule}")
#             created_count += 1

#     print(f"Import complete. Created: {created_count}, Skipped: {skipped_count}")
