from rest_framework import serializers
from .models import Document, DocumentType

class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Document
        fields = '__all__'

    def validate_file(self, file):
        """Validate the uploaded file based on document type."""
        document_type = self.initial_data.get('document_type', '')

        # Define allowed file types
        allowed_types = {
            DocumentType.PROFILE_PICTURE: ['image/jpeg', 'image/png', 'image/webp'],
            DocumentType.TECHNICAL_SHEET: ['application/pdf'],
        }

        # Check if document_type is valid
        if document_type not in allowed_types:
            raise serializers.ValidationError("Invalid document type.")

        # Validate MIME type
        if file.content_type not in allowed_types[document_type]:
            raise serializers.ValidationError(f"Invalid file type for {document_type}. Allowed: {allowed_types[document_type]}")

        return file
