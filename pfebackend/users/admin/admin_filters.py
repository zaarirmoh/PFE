from django.contrib import admin
from users.models import Student


class AcademicProgramYearFilter(admin.SimpleListFilter):
    title = 'Academic Year'
    parameter_name = 'academic_year'
    
    def lookups(self, request, model_admin):
        return [
            ('1CP', '1CP'),
            ('2CP', '2CP'),
            ('1CS', '1CS'),
            ('2CS', '2CS'),
            ('3CS', '3CS'),
        ]
    
    def queryset(self, request, queryset):
        if not self.value():
            return queryset
            
        if self.value() == '1CP':
            return queryset.filter(
                student__academic_program='preparatory',
                student__current_year=1
            )
        elif self.value() == '2CP':
            return queryset.filter(
                student__academic_program='preparatory',
                student__current_year=2
            )
        elif self.value() == '1CS':
            return queryset.filter(
                student__academic_program='superior',
                student__current_year=1
            )
        elif self.value() == '2CS':
            return queryset.filter(
                student__academic_program='superior',
                student__current_year=2
            )
        elif self.value() == '3CS':
            return queryset.filter(
                student__academic_program='superior',
                student__current_year=3
            )
        return queryset
