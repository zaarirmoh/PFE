from django.contrib import admin
from users.models import Student, Teacher, Administrator

class StudentProfileInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name = "Student Profile"
    verbose_name_plural = "Student Profile"

class TeacherProfileInline(admin.StackedInline):
    model = Teacher
    can_delete = False
    verbose_name = "Teacher Profile"
    verbose_name_plural = "Teacher Profile"

class AdministratorProfileInline(admin.StackedInline):
    model = Administrator
    can_delete = False
    verbose_name = "Administrator Profile"
    verbose_name_plural = "Administrator Profile"
