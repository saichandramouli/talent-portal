from django.db import models
from django.conf import settings
from teams.models import TechnologyStack

class Candidate(models.Model):
    profile_photo = models.ImageField(
        upload_to='candidates/',
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=255)
    years_of_experience = models.PositiveIntegerField(help_text="Years of professional experience")
    rate_card = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Rate card in USD (hourly/monthly)"
    )
    technical_stack = models.ManyToManyField(
        TechnologyStack,
        related_name='candidates'
    )
    location = models.CharField(max_length=255)
    availability = models.CharField(
        max_length=100,
        help_text="e.g. Immediate, 2 Weeks Notice, 1 Month Notice"
    )
    summary = models.TextField(help_text="Summary or notes about the candidate")
    
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.years_of_experience} yrs exp)"
