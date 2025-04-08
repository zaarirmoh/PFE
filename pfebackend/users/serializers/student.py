from rest_framework import serializers
from users.models import Student, StudentSkill

class StudentSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSkill
        fields = ('name', 'proficiency_level')
        
class StudentSerializer(serializers.ModelSerializer):
    skills = StudentSkillSerializer(many=True, read_only=True)
    class Meta:
        model = Student
        fields = (
            'matricule',
            'enrollment_year',
            'academic_program',
            'current_year',
            'speciality',
            'academic_status',
            'skills',
        )
        
    def create(self, validated_data):
        # If skills are provided during student creation
        skills_data = self.context.get('skills', [])
        student = super().create(validated_data)
        
        for skill_data in skills_data:
            StudentSkill.objects.create(
                student=student, 
                name=skill_data.get('name'),
                proficiency_level=skill_data.get('proficiency_level', 'beginner')
            )
        
        return student
    
    def update(self, instance, validated_data):
        # Handle skills update if provided
        skills_data = self.context.get('skills')
        
        # Update base student fields
        instance = super().update(instance, validated_data)
        
        if skills_data is not None:
            # Clear existing skills
            instance.skills.all().delete()
            
            # Create new skills
            for skill_data in skills_data:
                StudentSkill.objects.create(
                    student=instance, 
                    name=skill_data.get('name'),
                    proficiency_level=skill_data.get('proficiency_level', 'beginner')
                )
        
        return instance
