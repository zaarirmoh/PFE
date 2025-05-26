from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from common.models import TimeStampedModel
from teams.models import Team
from themes.models import ThemeAssignment





class Defense(TimeStampedModel):
    """
    Model representing a defense (soutenance) with all relevant information
    including time, place, and jury members.
    """
    title = models.CharField(_("Title"), max_length=255)
    theme_assignment = models.ForeignKey(
        ThemeAssignment,
        on_delete=models.CASCADE,
        related_name="defenses",
        verbose_name=_("Theme Assignment")
    )
    # Add a team property for backward compatibility
    @property
    def team(self):
        return self.theme_assignment.team
    
    # Add a theme property for convenience
    @property
    def theme(self):
        return self.theme_assignment.theme
    
    jury = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='JuryMember',
        related_name='jury_in_defenses',
        verbose_name=_("Jury")
    )
    # Date and time information
    date = models.DateField(_("Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    
    # Location information
    location = models.CharField(_("Location"), max_length=255)
    room = models.CharField(_("Room"), max_length=100, blank=True)
    
    # Document URIs
    defense_uri = models.URLField(_("Defense URI"), blank=True)
    report_uri = models.URLField(_("Report URI"), blank=True)
    specifications_document_uri = models.URLField(_("Specifications Document URI"), blank=True)
    
    description = models.TextField(_("Description"), blank=True)

    # Status
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('postponed', _('Postponed')),
    ]
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    
    # Result (to be filled after the defense)
    result = models.TextField(_("Result"), blank=True)
    grade = models.CharField(_("Grade"), max_length=50, blank=True)
    
    
    def __str__(self):
        return f"{self.title} - {self.team.name} ({self.date} jury members)"
    
    
    class Meta:
        verbose_name = _("Defense")
        verbose_name_plural = _("Defenses")
        ordering = ['-date', '-start_time']


class JuryMember(models.Model):
    """Model representing a jury member for a defense."""
    defense = models.ForeignKey(
        Defense,
        on_delete=models.CASCADE,
        related_name="jury_members",
        verbose_name=_("Defense")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jury_participations",
        verbose_name=_("User")
    )

    is_president = models.BooleanField(_("Is President"), default=False)
    notes = models.TextField(_("Notes"), blank=True)
    
    def __str__(self):
        president_info = " - President" if self.is_president else ""
        return f"{self.user.get_full_name()}{president_info}"
    
    class Meta:
        verbose_name = _("Jury Member")
        verbose_name_plural = _("Jury Members")
        # unique_together = ('defense', 'user')
