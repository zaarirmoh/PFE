from django.contrib import admin
from users.models import Student


class AcademicYearFilter(admin.SimpleListFilter):
    title = 'Academic Year'
    parameter_name = 'academic_year'
    
    def lookups(self, request, model_admin):
        return [
            ('2', '2nd Year'),
            ('3', '3rd Year'),
            ('4siw', '4th Year SIW'),
            ('4isi', '4th Year ISI'),
            ('4iasd', '4th Year IASD'),
            ('5siw', '5th Year SIW'),
            ('5isi', '5th Year ISI'),
            ('5iasd', '5th Year IASD'),
        ]
    
    def queryset(self, request, queryset):
        if not self.value():
            return queryset
            
        return queryset.filter(student__current_year=self.value())