from rest_framework import viewsets, permissions, parsers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing uploaded documents.
    """

    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        operation_description="Upload a new document.",
        consumes=["multipart/form-data"],  # ✅ Specifies form-data for file uploads
        manual_parameters=[
            openapi.Parameter(
                "file", openapi.IN_FORM, description="File to upload", type=openapi.TYPE_FILE, required=True
            ),
        ],
        responses={201: DocumentSerializer()}
    )
    def create(self, request, *args, **kwargs):
        """ Upload a new document """
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """ Set the creator of the document before saving. """
        serializer.save(created_by=self.request.user)


