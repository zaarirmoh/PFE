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
    
    # Academic program choices
    PREPARATORY = 'preparatory'
    SUPERIOR = 'superior'
    
    ACADEMIC_PROGRAM_CHOICES = [
        (PREPARATORY, _('Preparatory')),
        (SUPERIOR, _('Superior')),
    ]
    
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
    academic_program = models.CharField(
        max_length=20,
        choices=ACADEMIC_PROGRAM_CHOICES,
        help_text=_("Academic program this timeline applies to")
    )
    academic_year = models.PositiveSmallIntegerField(
        help_text=_("Academic year this timeline applies to (1, 2, or 3)")
    )
    
    class Meta:
        ordering = ['academic_program', 'academic_year', 'start_date', 'timeline_type']
        verbose_name = _("Timeline")
        verbose_name_plural = _("Timelines")
        unique_together = [['timeline_type', 'academic_program', 'academic_year']]
    
    def __str__(self):
        return f"{self.name} ({self.get_academic_program_display()} Year {self.academic_year})"
    
    def clean(self):
        """Ensure timeline constraints are met."""
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
        
        # Validate academic_year based on academic_program
        if self.academic_program == self.PREPARATORY and self.academic_year not in [1, 2]:
            raise ValidationError(_("For preparatory program, academic year must be 1 or 2"))
        elif self.academic_program == self.SUPERIOR and self.academic_year not in [1, 2, 3]:
            raise ValidationError(_("For superior program, academic year must be 1, 2, or 3"))
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is run."""
        # Generate slug if not provided
        if not self.slug:
            self.slug = f"{self.timeline_type}-{self.academic_program}-{self.academic_year}"
        
        self.clean()
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"{self.name} (Year: {self.academic_year}, Program: {self.academic_program})"
    
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
    def get_current_timeline(cls, timeline_type, academic_program, academic_year):
        """
        Get the current timeline for the given type, program and year.
        
        Args:
            timeline_type (str): The type of timeline (groups, themes, etc.)
            academic_program (str): The academic program (preparatory, superior)
            academic_year (int): The academic year (1, 2, or 3)
            
        Returns:
            Timeline or None: The current timeline or None if no active timeline exists
        """
        try:
            return cls.objects.get(
                timeline_type=timeline_type,
                academic_program=academic_program,
                academic_year=academic_year,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            return None
