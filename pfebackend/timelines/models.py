from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

class Timeline(models.Model):
    """
    Model representing a timeline in the application.
    
    Timelines define periods where specific actions (e.g., group formation) are allowed.
    """
    # Timeline Types
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
    
    # Academic year choices - matching Student model
    ACADEMIC_YEAR_CHOICES = (
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4siw', '4th Year SIW'),
        ('4isi', '4th Year ISI'),
        ('4iasd', '4th Year IASD'),
        ('5siw', '5th Year SIW'),
        ('5isi', '5th Year ISI'),
        ('5iasd', '5th Year IASD'),
    )
    
    # Fields
    slug = models.CharField(
        max_length=50, 
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
    timeline_type = models.CharField(
        max_length=20,
        choices=TIMELINE_CHOICES,
        help_text=_("Type of timeline")
    )
    academic_year = models.CharField(
        max_length=5,
        choices=ACADEMIC_YEAR_CHOICES,
        help_text=_("Academic year this timeline applies to")
    )
    
    class Meta:
        ordering = ['academic_year', 'start_date', 'timeline_type']
        verbose_name = _("Timeline")
        verbose_name_plural = _("Timelines")
        unique_together = [['timeline_type', 'academic_year']]
    
    def __str__(self):
        return f"{self.name} ({self.get_academic_year_display()})"
    
    def clean(self):
        """Ensure timeline constraints are met."""
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is run."""
        # Generate slug if not provided
        if not self.slug:
            self.slug = f"{self.timeline_type}-{self.academic_year}"
        
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
            
    @classmethod
    def get_current_timeline(cls, timeline_type, academic_year):
        """
        Get the current timeline for the given type and year.
        
        Args:
            timeline_type (str): The type of timeline (groups, themes, etc.)
            academic_year (str): The academic year code ('2', '3', '4siw', etc.)
            
        Returns:
            Timeline or None: The current timeline or None if no active timeline exists
        """
        try:
            return cls.objects.get(
                timeline_type=timeline_type,
                academic_year=academic_year,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            return None