from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(
            email=email, 
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, first_name, last_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'administrator')
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Super user must have is_staff = True")
        
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Super user must have is_superuser = True")
        
        user = self.create_user(
            email, username, first_name, last_name, password, **extra_fields
        )
        
        return user
    
class User(AbstractBaseUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('administrator', 'Administrator')
    )
    
    
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(max_length=50, unique = True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    profile_picture_url = models.URLField(
        max_length=500, null=True, blank=True,
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png",
        help_text="URL of the user's profile picture"
    )
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)
    is_superuser = models.BooleanField(default = False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name','last_name','user_type',]

    objects = UserManager()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    
    def __str__(self):
        return f"{self.first_name} | {self.email}"