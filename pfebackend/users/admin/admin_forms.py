from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from unfold.forms import UserChangeForm as UnfoldUserChangeForm
from unfold.forms import UserCreationForm as UnfoldUserCreationForm
from users.models import User

class CustomUserChangeForm(UnfoldUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
        
class CustomUserCreationForm(UnfoldUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'user_type', 'password1', 'password2')
