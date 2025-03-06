from .user import CustomUserSerializer, CustomUserCreateSerializer
from .student import StudentSerializer
from .teacher import TeacherSerializer
from .administrator import AdministratorSerializer
from .base import BaseProfileSerializer

# Register all profile serializers
BaseProfileSerializer.register('student', StudentSerializer)
BaseProfileSerializer.register('teacher', TeacherSerializer)
BaseProfileSerializer.register('administrator', AdministratorSerializer)

# Make all serializers available from the package level
__all__ = [
    'CustomUserSerializer',
    'CustomUserCreateSerializer',
    'StudentSerializer',
    'TeacherSerializer',
    'AdministratorSerializer',
]