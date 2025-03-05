from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *

User = get_user_model()

class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ("id","email","username","first_name","last_name","password","user_type",)
        
    def create(self, validated_data):
        user = super().create(validated_data)
        user_type = validated_data.get('user_type')
        if user_type == 'student':
            Student.objects.create(user=user)
        elif user_type == 'teacher':
            Teacher.objects.create(user=user)
        elif user_type == 'administrator':
            Administrator.objects.create(user=user)
        return user
    
class UserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ("id","email","username","first_name","last_name","user_type",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.user_type == 'student':
            data.update({'profile': instance.student.__dict__})
        elif instance.user_type == 'teacher':
            data.update({'profile': instance.teacher.__dict__})
        elif instance.user_type == 'administrator':
            data.update({'profile': instance.administrator.__dict__})
        return data
        
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        return token