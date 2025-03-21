from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .base import BaseProfileSerializer

User = get_user_model()

class CustomUserCreateSerializer(UserCreateSerializer):
    profile = serializers.DictField(write_only=True)
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'user_type', 'profile','profile_picture_url', 'password')
        
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
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'user_type', 'profile','profile_picture_url')
        
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

