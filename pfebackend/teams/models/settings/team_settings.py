from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from common.models import AuditableModel
from users.models import Student

class TeamSettings(AuditableModel):
    """
    Settings for team configurations based on academic program and year combinations.
    These settings can be modified by administrators for each program-year pair.
    """
    DEFAULT_MAX_MEMBERS = 6
    MAX_ABSOLUTE_LIMIT = 20  # Absolute maximum that can't be exceeded
    
    academic_year = models.PositiveSmallIntegerField(
        help_text="Academic year these settings apply to"
    )
    academic_program = models.CharField(
        max_length=20, 
        choices=Student.ACADEMIC_PROGRAM_CHOICES,
        help_text="Academic program these settings apply to"
    )
    
    maximum_members = models.PositiveSmallIntegerField(
        default=DEFAULT_MAX_MEMBERS,
        validators=[
            MinValueValidator(1, message="Teams must allow at least 1 members"),
            MaxValueValidator(MAX_ABSOLUTE_LIMIT, message=f"Teams cannot exceed {MAX_ABSOLUTE_LIMIT} members")
        ],
        help_text="Maximum number of students allowed in a single team"
    )
    class Meta:
        unique_together = [('academic_year', 'academic_program')]
        verbose_name = "Team Settings"
        verbose_name_plural = "Team Settings"
        
    def __str__(self):
        return f"{self.academic_program} - Year {self.academic_year} Settings"
    
    def save(self, *args, **kwargs):
        """
        Override save method to clear cache
        """
        super().save(*args, **kwargs)
        # Clear cache for this specific program-year combination
        cache_key = self._get_cache_key(self.academic_program, self.academic_year)
        cache.delete(cache_key)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the settings object"""
        pass
    
    @staticmethod
    def _get_cache_key(program, year):
        """Generate a cache key for a specific program-year combination"""
        return f'team_settings_{program}_{year}'
    
    @classmethod
    def get_settings(cls, program, year):
        """
        Get the settings for a specific academic program and year.
        If no settings exist, create default settings for this program-year.
        
        Args:
            program: The academic program code
            year: The academic year number
            
        Returns:
            TeamSettings: The settings object for the given program-year
        """
        cache_key = cls._get_cache_key(program, year)
        
        # Try to get from cache first
        settings = cache.get(cache_key)
        if settings is None:
            try:
                settings = cls.objects.get(academic_program=program, academic_year=year)
            except cls.DoesNotExist:
                # Create new settings with defaults
                settings = cls(
                    academic_program=program,
                    academic_year=year,
                    maximum_members=cls.DEFAULT_MAX_MEMBERS,
                )
                settings.save()
            
            # Cache for 1 hour
            cache.set(cache_key, settings, 3600)
        
        return settings
    
    @classmethod
    def get_maximum_members(cls):
        """Helper method to quickly get the maximum_members setting"""
        return cls.get_settings().maximum_members