from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .base import BaseProfileSerializer

User = get_user_model()

class CustomUserCreateSerializer(UserCreateSerializer):
    profile = serializers.DictField(write_only=True)
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'user_type', 'profile', 'password')
        
    def validate(self, attrs):
        profile_data = attrs.pop("profile", None)
        if not profile_data:
            raise serializers.ValidationError({
                "profile": "Profile data is required for user creation."
            })
        self.context["profile_data"] = profile_data
        return super().validate(attrs)
    
    def create(self, validated_data):
        user_type = validated_data.get('user_type')
        profile_data = self.context.get("profile_data")
        
        # Create the base user first
        user = super().create(validated_data)
        
        # Get the appropriate profile serializer based on user type
        profile_serializer_class = BaseProfileSerializer.get_serializer_for_type(user_type)
        
        # Create the profile using the serializer
        profile_serializer = profile_serializer_class(data=profile_data)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save(user=user)
        
        return user

class CustomUserSerializer(UserSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'user_type', 'profile')
        
    def get_profile(self, instance):
        # Get the profile instance
        profile_instance = BaseProfileSerializer.get_profile_instance(instance)
        if not profile_instance:
            return {}
            
        # Get and use the appropriate serializer
        serializer_class = BaseProfileSerializer.get_serializer_for_type(instance.user_type)
        return serializer_class(profile_instance).data
    
    def update(self, instance, validated_data):
        profile_data = None
        if self.initial_data and 'profile' in self.initial_data:
            profile_data = self.initial_data.get('profile')
        
        # Update the base user instance
        instance = super().update(instance, validated_data)
        
        if profile_data:
            # Get the appropriate serializer class and profile instance
            profile_serializer_class = BaseProfileSerializer.get_serializer_for_type(instance.user_type)
            profile_instance = BaseProfileSerializer.get_profile_instance(instance)
            
            # Update (or create) the profile
            serializer = profile_serializer_class(
                instance=profile_instance,
                data=profile_data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=instance)
        
        return instance





# from djoser.serializers import UserCreateSerializer, UserSerializer
# from django.contrib.auth import get_user_model
# from rest_framework import serializers
# from users.serializers.administrator import AdministratorSerializer
# from users.serializers.student import StudentSerializer
# from users.serializers.teacher import TeacherSerializer
# from users.models.administrator import Administrator
# from users.models.student import Student
# from users.models.teacher import Teacher

# User = get_user_model()
    
# PROFILE_SERIALIZERS = {
#     'student': StudentSerializer,
#     'teacher': TeacherSerializer,
#     'administrator': AdministratorSerializer,
# }

# class CustomUserCreateSerializer(UserCreateSerializer):
#     profile = serializers.DictField(write_only=True)
#     class Meta(UserCreateSerializer.Meta):
#         model = User
#         fields = ('id','email','username','first_name','last_name','user_type','profile','password',)
        
#     def validate(self, attrs):
#         profile_data = attrs.pop("profile", None)
#         if not profile_data:
#             raise serializers.ValidationError({
#                 "profile": "Profile data is required for user creation."
#             })
#         self.context["profile_data"] = profile_data
#         return super().validate(attrs)
    
#     def create(self, validated_data):
#         user_type = validated_data.get('user_type')
#         profile_data = self.context.get("profile_data")
#         if not profile_data:
#             raise serializers.ValidationError({
#                 "profile": "Profile data is required for user creation."
#             })
#         user = super().create(validated_data)
#         profile_serializer_class = PROFILE_SERIALIZERS.get(user_type)
#         if not profile_serializer_class:
#             raise serializers.ValidationError("Invalid user type provided.")
#         profile_serializer = profile_serializer_class(data=profile_data)
#         profile_serializer.is_valid(raise_exception=True)
#         profile_serializer.save(user=user)
#         return user
    
# class CustomUserSerializer(UserSerializer):
#     profile = serializers.SerializerMethodField()
#     class Meta(UserSerializer.Meta):
#         model = User
#         fields = ('id','email','username','first_name','last_name','user_type','profile')
        
#     def get_profile(self, instance):
#         if instance.user_type == 'student':
#             try:
#                 return StudentSerializer(instance.student).data
#             except Student.DoesNotExist:
#                 return {}
#         elif instance.user_type == 'teacher':
#             try:
#                 return TeacherSerializer(instance.teacher).data
#             except Teacher.DoesNotExist:
#                 return {}
#         elif instance.user_type == 'administrator':
#             try:
#                 return AdministratorSerializer(instance.administrator).data
#             except Administrator.DoesNotExist:
#                 return {}
#         return {}
    
#     def update(self, instance, validated_data):
#         profile_data = validated_data.pop('profile', None)
#         instance = super().update(instance, validated_data)
#         if profile_data:
#             profile_serializer_class = PROFILE_SERIALIZERS.get(instance.user_type)
#             if not profile_serializer_class:
#                 raise serializers.ValidationError("Invalid user type provided.")
            
#             # Try to get the existing profile instance for updating; if not present, we'll pass None
#             profile_instance = None
#             if instance.user_type == 'student':
#                 try:
#                     profile_instance = instance.student
#                 except Student.DoesNotExist:
#                     profile_instance = None
#             elif instance.user_type == 'teacher':
#                 try:
#                     profile_instance = instance.teacher
#                 except Teacher.DoesNotExist:
#                     profile_instance = None
#             elif instance.user_type == 'administrator':
#                 try:
#                     profile_instance = instance.administrator
#                 except Administrator.DoesNotExist:
#                     profile_instance = None
            
#             # Use the appropriate serializer to update (or create) the profile
#             serializer = profile_serializer_class(
#                 instance=profile_instance,
#                 data=profile_data,
#                 partial=True  # PATCH supports partial updates
#             )
#             serializer.is_valid(raise_exception=True)
#             serializer.save(user=instance)
        
#         return instance
    