from django import forms
from django.contrib.auth import get_user_model
from .models import (
    CorporateClient, CorporateCandidate, JobRequirement,
    CandidateSubmission, RecruiterClientAssignment
)

User = get_user_model()


# ─── Admin Forms ─────────────────────────────────────────────────────────────

class CorporateClientUserForm(forms.ModelForm):
    """Create the User account linked to a Corporate Client."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'login@company.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class CorporateClientProfileForm(forms.ModelForm):
    """Create/Edit the CorporateClient profile."""

    class Meta:
        model = CorporateClient
        fields = ['company_name', 'company_website', 'industry', 'contact_phone', 'address', 'description']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC Technologies Pvt Ltd'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IT / Finance / Healthcare'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Office address'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
        }


class CorporateClientEditUserForm(forms.ModelForm):
    """Edit the User account of an existing Corporate Client."""

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Another user with this email already exists.')
        return email


class RecruiterAssignmentForm(forms.Form):
    """Multi-select form to assign recruiters to a corporate client."""
    recruiters = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='recruiter', is_active=True).order_by('full_name'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Assign Recruiters'
    )


# ─── Recruiter Forms ──────────────────────────────────────────────────────────

class JobRequirementForm(forms.ModelForm):
    class Meta:
        model = JobRequirement
        fields = ['job_title', 'required_skills', 'experience', 'location', 'rate_card',
                  'employment_type', 'description', 'status']
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Developer'}),
            'required_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                      'placeholder': 'List required skills, one per line or comma-separated'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5+ Years'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hyderabad / Remote / USA'}),
            'rate_card': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. $80/hr or $120k/yr'}),
            'employment_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Contract, Full-Time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                  'placeholder': 'Full job description / JD'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CorporateCandidateForm(forms.ModelForm):
    class Meta:
        model = CorporateCandidate
        fields = [
            'profile_photo', 'full_name', 'gender', 'email', 'phone',
            'total_experience', 'current_location', 'technology_stack',
            'current_company', 'rate_card', 'resume', 'bgv_verification',
            'evaluation_certificate', 'notes', 'status'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'candidate@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'total_experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6 Years'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bangalore'}),
            'technology_stack': forms.TextInput(attrs={'class': 'form-control',
                                                        'placeholder': 'e.g. SAP FICO, Python, React – any stack'}),
            'current_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current employer (optional)'}),
            'rate_card': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes…'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'resume': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'bgv_verification': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'evaluation_certificate': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

    def _validate_pdf_only(self, file_obj, field_name):
        if file_obj:
            if file_obj.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f"{field_name} file size should not exceed 10MB.")
            ext = file_obj.name.split('.')[-1].lower()
            if ext != 'pdf':
                raise forms.ValidationError(f"Unsupported format for {field_name}. Only PDF files are allowed.")
        return file_obj

    def clean_resume(self):
        return self._validate_pdf_only(self.cleaned_data.get('resume'), 'Resume')

    def clean_bgv_verification(self):
        return self._validate_pdf_only(self.cleaned_data.get('bgv_verification'), 'BGV Verification')

    def clean_evaluation_certificate(self):
        return self._validate_pdf_only(self.cleaned_data.get('evaluation_certificate'), 'Evaluation Certificate')


class CandidateSubmissionForm(forms.Form):
    """
    Form used by a recruiter to submit corporate candidates to a specific job.
    Allows selecting multiple candidates from their own pool.
    """
    candidates = forms.ModelMultipleChoiceField(
        queryset=CorporateCandidate.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label='Select Candidates to Submit'
    )

    def __init__(self, *args, recruiter=None, exclude_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = CorporateCandidate.objects.filter(recruiter=recruiter, status='active')
        if exclude_ids:
            qs = qs.exclude(id__in=exclude_ids)
        self.fields['candidates'].queryset = qs


class SubmissionStatusForm(forms.Form):
    """Allow recruiter or client to update submission status."""
    STATUS_CHOICES = CandidateSubmission.STATUS_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional comments…'})
    )
