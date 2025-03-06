from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseProfileSerializer:
    """
    Base class for defining profile serializer registration.
    This allows for centralized registration of profile serializers.
    """
    _registry = {}

    @classmethod
    def register(cls, user_type, serializer_class):
        """Register a profile serializer for a specific user type"""
        cls._registry[user_type] = serializer_class
        
    @classmethod
    def get_serializer_for_type(cls, user_type):
        """Get the appropriate serializer for a user type"""
        serializer = cls._registry.get(user_type)
        if not serializer:
            raise serializers.ValidationError(f"Invalid user type: {user_type}")
        return serializer
        
    @classmethod
    def get_profile_instance(cls, user_instance):
        """Get profile instance based on user type"""
        user_type = user_instance.user_type
        if user_type == 'student':
            return getattr(user_instance, 'student', None)
        elif user_type == 'teacher':
            return getattr(user_instance, 'teacher', None)
        elif user_type == 'administrator':
            return getattr(user_instance, 'administrator', None)
        return None