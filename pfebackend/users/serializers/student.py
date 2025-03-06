from rest_framework import serializers
from users.models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = (
            'matricule',
            'enrollment_year',
            'academic_program',
            'current_year',
            'speciality',
            'academic_status',
        )
