from django.db import models
from common.models import TimeStampedModel
# from .student import Student

class ExcelUpload(TimeStampedModel):
    ACADEMIC_YEAR_CHOICES = (
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4siw', '4th Year SIW'),
        ('4isi', '4th Year ISI'),
        ('4iasd', '4th Year IASD'),
        ('5siw', '5th Year SIW'),
        ('5isi', '5th Year ISI'),
        ('5iasd', '5th Year IASD'),
    )
    
    file = models.FileField(upload_to='uploads/excels/')
    academic_year = models.CharField(max_length=10, choices=ACADEMIC_YEAR_CHOICES, default='2')
    
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from ..student_importer_test_servic import import_students_from_excel, create_students_from_excel
        if self.academic_year == '1':
            create_students_from_excel(file_path=self.file.path, academic_year=self.academic_year)
        else:
            import_students_from_excel(file_path=self.file.path,academic_year=self.academic_year)
