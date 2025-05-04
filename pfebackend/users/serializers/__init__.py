from .user import CustomUserSerializer, CustomUserCreateSerializer
from .student import StudentSerializer, StudentSkillSerializer
from .teacher import TeacherSerializer
from .administrator import AdministratorSerializer
from .base import BaseProfileSerializer
from .external_user import ExternalUserSerializer

# Register all profile serializers
BaseProfileSerializer.register('student', StudentSerializer)
BaseProfileSerializer.register('teacher', TeacherSerializer)
BaseProfileSerializer.register('administrator', AdministratorSerializer)
BaseProfileSerializer.register('external_user', ExternalUserSerializer)

# Make all serializers available from the package level
__all__ = [
    'CustomUserSerializer',
    'CustomUserCreateSerializer',
    'StudentSerializer',
    'TeacherSerializer',
    'AdministratorSerializer',
    'ExternalUserSerializer',
    'StudentSkillSerializer',
]