from rest_framework import serializers
from users.models import ExternalUser

class ExternalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalUser
        fields = (
            'external_user_type',
        )