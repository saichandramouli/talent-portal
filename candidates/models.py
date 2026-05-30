from django.db import models
from django.conf import settings
from teams.models import TechnologyStack

class JobTitle(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

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
    summary = models.TextField(blank=True, default='', help_text="Summary or notes about the candidate")
    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates'
    )
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='candidates'
    )
    
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    
    is_on_hold = models.BooleanField(
        default=False,
        help_text="If checked, this candidate is on hold and invisible to clients."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.years_of_experience} yrs exp)"
