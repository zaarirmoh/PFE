from django.contrib import admin
from users.models import Student, Teacher, Administrator, ExternalUser
from unfold import admin as UnfoldAdmin

class StudentProfileInline(UnfoldAdmin.StackedInline):
    model = Student
    can_delete = False
    verbose_name = "Student Profile"
    verbose_name_plural = "Student Profile"
    tab = True

class TeacherProfileInline(UnfoldAdmin.StackedInline):
    model = Teacher
    can_delete = False
    verbose_name = "Teacher Profile"
    verbose_name_plural = "Teacher Profile"
    tab = True

class ExternalUserProfileInline(UnfoldAdmin.StackedInline):
    model = ExternalUser
    can_delete = False
    verbose_name = "External User Profile"
    verbose_name_plural = "External User Profile"
    tab = True

class AdministratorProfileInline(UnfoldAdmin.StackedInline):
    model = Administrator
    can_delete = False
    verbose_name = "Administrator Profile"
    verbose_name_plural = "Administrator Profile"
    tab = True
