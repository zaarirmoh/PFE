from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError


class Timeline(models.Model):
    """
    Model representing a timeline in the application.
    
    Timelines are used to control the flow of the application based on
    specific periods defined by start and end dates.
    """
    # Timeline types as class constants
    GROUPS = 'groups'
    THEMES = 'themes'
    WORK = 'work'
    SOUTENANCE = 'soutenance'
    
    TIMELINE_CHOICES = [
        (GROUPS, _('Groups')),
        (THEMES, _('Themes')),
        (WORK, _('Work')),
        (SOUTENANCE, _('Soutenance')),
    ]
    
    # Fields
    slug = models.CharField(
        max_length=20, 
        choices=TIMELINE_CHOICES, 
        unique=True,
        help_text=_("Unique identifier for the timeline")
    )
    name = models.CharField(
        max_length=100,
        help_text=_("Display name of the timeline")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Detailed description of the timeline's purpose")
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text=_("When this timeline becomes active")
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When this timeline ends (leave blank for open-ended)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this timeline is currently enabled")
    )
    
    class Meta:
        ordering = ['start_date', 'slug']
        verbose_name = _("Timeline")
        verbose_name_plural = _("Timelines")
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate the model data."""
        # Ensure end_date is after start_date if provided
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is run."""
        self.clean()
        super().save(*args, **kwargs)
        
    @property
    def is_current(self):
        """
        Check if the timeline is currently active based on dates.
        
        Returns:
            bool: True if the timeline is within its active date range, False otherwise.
        """
        now = timezone.now()
        
        # Timeline is not active
        if not self.is_active:
            return False
            
        # Timeline with both start and end dates
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date
            
        # Timeline with only start date (open-ended)
        elif self.start_date:
            return self.start_date <= now
            
        # Timeline with neither start nor end date
        return False
    
    @property
    def status(self):
        """
        Get the current status of the timeline.
        
        Returns:
            str: 'upcoming', 'active', 'expired', or 'inactive'
        """
        if not self.is_active:
            return 'inactive'
            
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return 'upcoming'
        elif self.end_date and now > self.end_date:
            return 'expired'
        else:
            return 'active'
