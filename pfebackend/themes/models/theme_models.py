from django.db import models
from django.core.exceptions import ValidationError
from common.models import AuditableModel
from users.models import User
from documents.models import Document

class Theme(AuditableModel):
    """
    Represents a theme proposed by teachers, associated with a specific academic year and program.
    """
    title = models.CharField(max_length=255)
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposed_themes")
    co_supervisors = models.ManyToManyField(User, related_name="co_supervised_themes", blank=True)
    specialty = models.CharField(
        max_length=100,
        choices=[
            ('IASD', 'IASD'),
            ('SIW', 'SIW'),
            ('ISI', 'ISI'),
            ('1CS', '1CS'),
            ('2CPI', '2CPI'),
        ]
    )
    description = models.TextField()
    tools = models.TextField(help_text="Enter tools")
    documents = models.ManyToManyField(Document, related_name="themes", blank=True)

    # Academic year and program
    academic_year = models.PositiveSmallIntegerField(help_text="Must match the academic year of the linked Timeline")
    academic_program = models.CharField(
        max_length=20,
        choices=[
            ('preparatory', 'Preparatory'),
            ('superior', 'Superior'),
        ],
        help_text="Must match the academic program of the linked Timeline"
    )

    def clean(self):

        if self.proposed_by.user_type != "teacher":
            raise ValidationError({"proposed_by": "Only teachers can propose themes."})

    def save(self, *args, **kwargs):
        """
        Validate `co_supervisors` only after saving.
        """
        super().save(*args, **kwargs)  # Save first, so Many-to-Many relationships are available

        invalid_supervisors = [user for user in self.co_supervisors.all() if user.user_type != "teacher"]
        if invalid_supervisors:
            invalid_ids = [user.id for user in invalid_supervisors]
            raise ValidationError({"co_supervisors": f"These users are not teachers: {invalid_ids}"})

    def __str__(self):
        return f"{self.title} (Year: {self.academic_year}, Program: {self.academic_program})"




