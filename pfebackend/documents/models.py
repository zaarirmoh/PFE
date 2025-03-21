from django.db import models
from common.models import AuditableModel 

class DocumentType(models.TextChoices):
    TECHNICAL_SHEET = "technical_sheet", "Technical SHEET"
    PROFILE_PICTURE = "profile_picture", "Profile Picture"
    LIVRABLE = "livrable", "Livrable"

class Document(AuditableModel): 
    title = models.CharField(max_length=255,blank=True)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)

    def __str__(self):
        return f"{self.title} ({self.document_type})"
