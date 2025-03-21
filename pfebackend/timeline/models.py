# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.utils import timezone
# from django.core.exceptions import ValidationError


# class Timeline(models.Model):
#     """
#     Model representing a timeline in the application.
    
#     Timelines are used to control the flow of the application based on
#     specific periods defined by start and end dates.
#     """
#     # Timeline types as class constants
#     GROUPS = 'groups'
#     THEMES = 'themes'
#     WORK = 'work'
#     SOUTENANCE = 'soutenance'
    
#     TIMELINE_CHOICES = [
#         (GROUPS, _('Groups')),
#         (THEMES, _('Themes')),
#         (WORK, _('Work')),
#         (SOUTENANCE, _('Soutenance')),
#     ]
    
#     # Fields
#     slug = models.CharField(
#         max_length=20, 
#         choices=TIMELINE_CHOICES, 
#         unique=True,
#         help_text=_("Unique identifier for the timeline")
#     )
#     name = models.CharField(
#         max_length=100,
#         help_text=_("Display name of the timeline")
#     )
#     description = models.TextField(
#         blank=True,
#         help_text=_("Detailed description of the timeline's purpose")
#     )
#     start_date = models.DateTimeField(
#         default=timezone.now,
#         help_text=_("When this timeline becomes active")
#     )
#     end_date = models.DateTimeField(
#         null=True, 
#         blank=True,
#         help_text=_("When this timeline ends (leave blank for open-ended)")
#     )
#     is_active = models.BooleanField(
#         default=True,
#         help_text=_("Whether this timeline is currently enabled")
#     )
    
#     class Meta:
#         ordering = ['start_date', 'slug']
#         verbose_name = _("Timeline")
#         verbose_name_plural = _("Timelines")
    
#     def __str__(self):
#         return self.name
    
#     def clean(self):
#         """Validate the model data."""
#         # Ensure end_date is after start_date if provided
#         if self.end_date and self.start_date and self.end_date <= self.start_date:
#             raise ValidationError(_("End date must be after start date"))
    
#     def save(self, *args, **kwargs):
#         """Override save to ensure validation is run."""
#         self.clean()
#         super().save(*args, **kwargs)
        
#     @property
#     def is_current(self):
#         """
#         Check if the timeline is currently active based on dates.
        
#         Returns:
#             bool: True if the timeline is within its active date range, False otherwise.
#         """
#         now = timezone.now()
        
#         # Timeline is not active
#         if not self.is_active:
#             return False
            
#         # Timeline with both start and end dates
#         if self.start_date and self.end_date:
#             return self.start_date <= now <= self.end_date
            
#         # Timeline with only start date (open-ended)
#         elif self.start_date:
#             return self.start_date <= now
            
#         # Timeline with neither start nor end date
#         return False
    
#     @property
#     def status(self):
#         """
#         Get the current status of the timeline.
        
#         Returns:
#             str: 'upcoming', 'active', 'expired', or 'inactive'
#         """
#         if not self.is_active:
#             return 'inactive'
            
#         now = timezone.now()
        
#         if self.start_date and now < self.start_date:
#             return 'upcoming'
#         elif self.end_date and now > self.end_date:
#             return 'expired'
#         else:
#             return 'active'


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
    
    # Specialty Choices
    SPECIALTY_CHOICES = [
        ('IASD', 'IASD'),
        ('SIW', 'SIW'),
        ('ISI', 'ISI'),
        ('1CS', '1CS'),
        ('2CPI', '2CPI'),
    ]

    # Academic Programs
    ACADEMIC_PROGRAM_CHOICES = [
        ('preparatory', 'Preparatory'),
        ('superior', 'Superior'),
    ]

    # Fields
    slug = models.CharField(
        max_length=20, 
        choices=TIMELINE_CHOICES, 
        unique=True,
        help_text=_("Unique identifier for the timeline")
    )
    name = models.CharField(max_length=100, help_text=_("Display name of the timeline"))
    description = models.TextField(blank=True, help_text=_("Detailed description of the timeline's purpose"))
    start_date = models.DateTimeField(default=timezone.now, help_text=_("When this timeline becomes active"))
    end_date = models.DateTimeField(null=True, blank=True, help_text=_("When this timeline ends (leave blank for open-ended)"))
    is_active = models.BooleanField(default=True, help_text=_("Whether this timeline is currently enabled"))

    # New Fields
    academic_year = models.PositiveSmallIntegerField(help_text="Academic year applicable to this timeline")
    academic_program = models.CharField(max_length=20, choices=ACADEMIC_PROGRAM_CHOICES, help_text="Department/academic program for this timeline")
    specialty = models.CharField(max_length=20, choices=SPECIALTY_CHOICES, default='common', help_text="Specialty for students in this timeline")

    class Meta:
        ordering = ['start_date', 'slug']
        verbose_name = _("Timeline")
        verbose_name_plural = _("Timelines")

    def clean(self):
        """Ensure timeline constraints are met."""
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
        
        # Enforce specialty rules
        if self.academic_program == 'preparatory' and self.academic_year== 2:
            self.specialty = '2CPI'
        elif self.academic_program == 'superior' and self.academic_year == 1:
            self.specialty = '1CS'
        elif self.academic_program == 'superior' and self.academic_year in [2, 3] and self.specialty not in ('ISI','SIW','IASD'):
            raise ValidationError(_("Superior students in Year 2 or 3 must have a specialty"))

    def save(self, *args, **kwargs):
        """Override save to validate data before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Year: {self.academic_year}, Program: {self.academic_program}, Specialty: {self.specialty})"
    
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


