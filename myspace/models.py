from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class CorporateClient(models.Model):
    """
    Represents a corporate company that is a client of the talent portal.
    Created by Admin only – cannot self-register.
    Linked one-to-one with a User whose role='corporate_client'.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='corporate_client_profile',
        limit_choices_to={'role': 'corporate_client'}
    )
    company_name = models.CharField(max_length=255, help_text='Company / Organisation Name')
    company_website = models.URLField(max_length=300, blank=True, default='')
    industry = models.CharField(max_length=255, blank=True, default='')
    contact_phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']
        verbose_name = 'Corporate Client'
        verbose_name_plural = 'Corporate Clients'

    def __str__(self):
        return self.company_name

    @property
    def assigned_recruiters(self):
        return [a.recruiter for a in self.recruiter_assignments.select_related('recruiter')]


class RecruiterClientAssignment(models.Model):
    """
    Maps a Recruiter (User) to a CorporateClient.
    Admin manages these assignments.
    """
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_assignments',
        limit_choices_to={'role': 'recruiter'}
    )
    client = models.ForeignKey(
        CorporateClient,
        on_delete=models.CASCADE,
        related_name='recruiter_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('recruiter', 'client')
        ordering = ['-assigned_at']
        verbose_name = 'Recruiter–Client Assignment'

    def __str__(self):
        return f"{self.recruiter.full_name} → {self.client.company_name}"


class CorporateCandidate(models.Model):
    """
    Completely separate from the public Candidate model.
    No tech-stack or team restrictions.
    Managed solely within My Space by recruiters.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('placed', 'Placed'),
        ('inactive', 'Inactive'),
    ]

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='corporate_candidates',
        limit_choices_to={'role': 'recruiter'}
    )
    profile_photo = models.ImageField(
        upload_to='corporate_candidates/photos/',
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, default='')
    total_experience = models.CharField(
        max_length=100,
        help_text='e.g. 5 Years, 8.5 Years'
    )
    current_location = models.CharField(max_length=255)
    technology_stack = models.CharField(
        max_length=255,
        help_text='e.g. SAP, Python, React, DevOps – free-form text, no restrictions'
    )
    current_company = models.CharField(max_length=255, blank=True, default='')
    rate_card = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Rate card in USD'
    )
    resume = models.FileField(
        upload_to='corporate_candidates/resumes/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    bgv_verification = models.FileField(
        upload_to='corporate_candidates/bgv_verifications/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    evaluation_certificate = models.FileField(
        upload_to='corporate_candidates/evaluation_certificates/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Corporate Candidate'

    def __str__(self):
        return f"{self.full_name} ({self.technology_stack})"

    @property
    def profile_photo_optimized_url(self):
        if not self.profile_photo:
            return ''
        url = self.profile_photo.url
        if 'upload/' in url:
            return url.replace('upload/', 'upload/f_auto,q_auto/')
        return url

    @property
    def profile_photo_thumbnail_url(self):
        if not self.profile_photo:
            return ''
        url = self.profile_photo.url
        if 'upload/' in url:
            return url.replace('upload/', 'upload/f_auto,q_auto,w_150,h_150,c_fill/')
        return url

    @property
    def rate_card_inr(self):
        return int(float(self.rate_card) * 95.75)


class JobRequirement(models.Model):
    """
    A job requirement / JD raised by a Corporate Client.
    Recruiters create these on behalf of the client.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('on_hold', 'On Hold'),
        ('filled', 'Filled'),
    ]

    client = models.ForeignKey(
        CorporateClient,
        on_delete=models.CASCADE,
        related_name='job_requirements'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_job_requirements'
    )
    job_title = models.CharField(max_length=255)
    required_skills = models.TextField()
    experience = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    rate_card = models.CharField(max_length=100, help_text='e.g. $80/hr or $120k/yr')
    employment_type = models.CharField(max_length=100, help_text='e.g. Contract, Full-Time, Part-Time')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Requirement'

    def __str__(self):
        return f"{self.job_title} @ {self.client.company_name}"


class CandidateSubmission(models.Model):
    """
    Links a CorporateCandidate to a JobRequirement.
    Represents a recruiter submitting a candidate for a specific job.
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('viewed', 'Viewed'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    candidate = models.ForeignKey(
        CorporateCandidate,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate_submissions'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['-created_at']
        verbose_name = 'Candidate Submission'

    def __str__(self):
        return f"{self.candidate.full_name} → {self.job.job_title}"


class SubmissionStatusHistory(models.Model):
    """
    Immutable log of status changes on a CandidateSubmission.
    """
    submission = models.ForeignKey(
        CandidateSubmission,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submission_status_changes'
    )
    comments = models.TextField(blank=True, default='')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Submission Status History'

    def __str__(self):
        return f"{self.submission} → {self.status} at {self.changed_at:%Y-%m-%d %H:%M}"


class CandidateCart(models.Model):
    """
    Corporate Client selects (shortlists) a candidate for a specific job.
    Adding to cart triggers an email notification to the recruiter.
    """
    client = models.ForeignKey(
        CorporateClient,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    job = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    candidate = models.ForeignKey(
        CorporateCandidate,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'job', 'candidate')
        ordering = ['-created_at']
        verbose_name = 'Candidate Cart Item'

    def __str__(self):
        return f"{self.client.company_name} – {self.candidate.full_name} for {self.job.job_title}"


class CorporateCredentialRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    client = models.ForeignKey(
        CorporateClient,
        on_delete=models.CASCADE,
        related_name='credential_requests'
    )
    candidate = models.ForeignKey(
        CorporateCandidate,
        on_delete=models.CASCADE,
        related_name='credential_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'candidate')
        ordering = ['-created_at']
        verbose_name = 'Corporate Credential Request'
        verbose_name_plural = 'Corporate Credential Requests'

    def __str__(self):
        return f"Request by {self.client.company_name} for {self.candidate.full_name} ({self.status})"

