# from rest_framework import serializers
# from .models import Theme
# from documents.models import Document
# from documents.serializers import DocumentSerializer
# from users.models import User

# class ThemeSerializer(serializers.ModelSerializer):
#     """
#     Serializer for the Theme model.
#     """
#     documents = DocumentSerializer(many=True, read_only=True)
#     document_ids = serializers.PrimaryKeyRelatedField(
#         queryset=Document.objects.all(), many=True, write_only=True, required=False
#     )
#     co_supervisors = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.filter(user_type="teacher"), many=True, required=False, write_only=True
#     )

#     class Meta:
#         model = Theme
#         fields = '__all__'
#         read_only_fields = ["proposed_by"]  # Ensure `proposed_by` is set automatically

#     def validate(self, data):
#         """
#         Ensure the requesting user is a teacher before assigning them as `proposed_by`.
#         """
#         request = self.context.get("request")
#         if request and request.user:
#             if request.user.user_type != "teacher":
#                 raise serializers.ValidationError("Only teachers can propose themes.")
#             data["proposed_by"] = request.user  # Assign the current user as `proposed_by`
#         return data

#     def create(self, validated_data):
#         """
#         Override create to handle Many-to-Many relationships properly.
#         """
#         co_supervisors_data = validated_data.pop('co_supervisors', [])  # Get co-supervisors
#         document_ids = validated_data.pop('document_ids', [])

#         theme = Theme.objects.create(**validated_data)  # Create theme
#         theme.co_supervisors.set(co_supervisors_data)  # ✅ Use `.set()` for Many-to-Many
#         theme.documents.set(document_ids)  # ✅ Use `.set()` for Many-to-Many

#         return theme
from rest_framework import serializers
from ..models.theme_models import Theme
from documents.models import Document
from documents.serializers import DocumentSerializer
from users.models import User
from users.serializers import CustomUserSerializer

class ThemeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Theme model.
    """
    documents = DocumentSerializer(many=True, read_only=True)

    # Accept document IDs for write
    document_ids = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), many=True, write_only=True, required=False
    )

    # Accept co-supervisor IDs for write
    co_supervisors = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type="teacher"), many=True, write_only=True, required=False
    )

    # Return co-supervisor full objects for read (same field name)
    co_supervisors = CustomUserSerializer(many=True, read_only=True)

    # proposed_by: override to return full user info instead of just ID
    proposed_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = Theme
        fields = '__all__'
        read_only_fields = ["proposed_by"]

    def validate(self, data):
        """
        Ensure the requesting user is a teacher before assigning them as `proposed_by`.
        """
        request = self.context.get("request")
        if request and request.user:
            if request.user.user_type != "teacher":
                raise serializers.ValidationError("Only teachers can propose themes.")
            data["proposed_by"] = request.user
        return data

    def create(self, validated_data):
        """
        Override create to handle Many-to-Many relationships properly.
        """
        co_supervisors = validated_data.pop('co_supervisors', [])
        document_ids = validated_data.pop('document_ids', [])
        theme = Theme.objects.create(**validated_data)
        theme.co_supervisors.set(co_supervisors)
        theme.documents.set(document_ids)

        return theme



