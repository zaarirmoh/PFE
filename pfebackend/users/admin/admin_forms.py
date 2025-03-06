from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from users.models import User

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
        
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'user_type', 'password1', 'password2')
