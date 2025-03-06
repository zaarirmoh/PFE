from rest_framework import serializers
from users.models import Administrator

class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = (
            'role_description',
        )