from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from common.models import AuditableModel

class TeamSettings(AuditableModel):
    """
    Global settings for team configurations that can be modified by administrators.
    Uses a singleton pattern to ensure only one settings object exists.
    """
    DEFAULT_MAX_MEMBERS = 6
    MAX_ABSOLUTE_LIMIT = 20  # Absolute maximum that can't be exceeded
    
    maximum_members = models.PositiveSmallIntegerField(
        default=DEFAULT_MAX_MEMBERS,
        validators=[
            MinValueValidator(2, message="Teams must allow at least 2 members"),
            MaxValueValidator(MAX_ABSOLUTE_LIMIT, message=f"Teams cannot exceed {MAX_ABSOLUTE_LIMIT} members")
        ],
        help_text="Maximum number of students allowed in a single team"
    )
    
    allow_cross_program_teams = models.BooleanField(
        default=False,
        help_text="If enabled, students from different programs can join the same team"
    )
    
    allow_cross_year_teams = models.BooleanField(
        default=False,
        help_text="If enabled, students from different academic years can join the same team"
    )
    
    class Meta:
        verbose_name = "Team Settings"
        verbose_name_plural = "Team Settings"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one instance exists and invalidate cache after saving
        """
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cache to force refresh
        cache.delete('team_settings')
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the settings object"""
        pass
    
    @classmethod
    def get_settings(cls):
        """
        Get the current settings, using cached version if available.
        If no settings object exists, create one with defaults.
        """
        # Try to get from cache first
        settings = cache.get('team_settings')
        if settings is None:
            try:
                settings = cls.objects.get(pk=1)
            except cls.DoesNotExist:
                settings = cls.objects.create(pk=1)
            # Cache for 1 hour
            cache.set('team_settings', settings, 3600)
        return settings
    
    @classmethod
    def get_maximum_members(cls):
        """Helper method to quickly get the maximum_members setting"""
        return cls.get_settings().maximum_members