from django import forms
from .models import Candidate, JobTitle, Skill
from teams.models import TechnologyStack

class JobTitleForm(forms.ModelForm):
    class Meta:
        model = JobTitle
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Engineer'}),
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python'}),
        }

class CandidateForm(forms.ModelForm):
    employment_type = forms.MultipleChoiceField(
        choices=[
            ('Full Time', 'Full Time'),
            ('Contract', 'Contract'),
            ('Remote', 'Remote'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Employment Type"
    )
    availability = forms.MultipleChoiceField(
        choices=[
            ('Immediate', 'Immediate'),
            ('15 Days', '15 Days'),
            ('1 Month', '1 Month'),
            ('2 Months', '2 Months'),
            ('3 Months', '3 Months'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Notice Period"
    )

    class Meta:
        model = Candidate
        fields = [
            'profile_photo', 'full_name', 'gender', 'job_title', 'skills', 'years_of_experience',
            'rate_card', 'salary_inr', 'employment_type', 'technical_stack', 'location', 'availability', 'is_on_hold',
            'resume', 'bgv_verification', 'evaluation_certificate'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Candidate Full Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g. 5'}),
            'rate_card': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'}),
            'salary_inr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 1200000.00'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New York, NY'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_on_hold': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'technical_stack': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'resume': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bgv_verification': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'evaluation_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Load initial values for MultipleChoiceFields
        if self.instance and self.instance.pk:
            if self.instance.employment_type:
                self.initial['employment_type'] = [x.strip() for x in self.instance.employment_type.split(',') if x.strip()]
            if self.instance.availability:
                self.initial['availability'] = [x.strip() for x in self.instance.availability.split(',') if x.strip()]

        # If user is recruiter, restrict the choices of tech stack to their team's stacks
        if self.user and self.user.role == 'recruiter':
            self.fields['technical_stack'].error_messages['invalid_choice'] = "You are not authorized to upload candidates outside your assigned technology stack."
            if self.user.team:
                self.fields['technical_stack'].queryset = self.user.team.technology_stacks.all()
            else:
                self.fields['technical_stack'].queryset = TechnologyStack.objects.none()

    def clean_technical_stack(self):
        selected_stacks = self.cleaned_data.get('technical_stack')
        if not self.user:
            return selected_stacks
            
        # Admin can select any stack
        if self.user.role == 'admin' or self.user.is_superuser:
            return selected_stacks
            
        # Recruiter checks
        if self.user.role == 'recruiter':
            if not self.user.team:
                raise forms.ValidationError("You must be assigned to a team before you can upload candidates.")
                
            allowed_stack_ids = set(self.user.team.technology_stacks.values_list('id', flat=True))
            for stack in selected_stacks:
                if stack.id not in allowed_stack_ids:
                    raise forms.ValidationError("You are not authorized to upload candidates outside your assigned technology stack.")
                    
        return selected_stacks
        
    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # File size limit (e.g. 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file size should not exceed 5MB.")
            # File type verification
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise forms.ValidationError("Unsupported image format. Allowed formats: JPG, JPEG, PNG, WEBP.")
        return photo

    def _validate_pdf_only(self, file_obj, field_name):
        if file_obj:
            if file_obj.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f"{field_name} file size should not exceed 10MB.")
            ext = file_obj.name.split('.')[-1].lower()
            if ext != 'pdf':
                raise forms.ValidationError(f"Unsupported format for {field_name}. Only PDF files are allowed.")
        return file_obj

    def clean(self):
        cleaned_data = super().clean()
        emp_types = cleaned_data.get('employment_type', [])
        rate_card = cleaned_data.get('rate_card')
        salary_inr = cleaned_data.get('salary_inr')

        if 'Full Time' in emp_types:
            if not salary_inr:
                self.add_error('salary_inr', 'Salary in INR per annum is required for Full Time employment.')
        if 'Contract' in emp_types or 'Remote' in emp_types:
            if not rate_card:
                self.add_error('rate_card', 'Rate card in USD per hour is required for Contract or Remote employment.')

        return cleaned_data

    def save(self, commit=True):
        candidate = super().save(commit=False)
        emp_types = self.cleaned_data.get('employment_type', [])
        availabilities = self.cleaned_data.get('availability', [])
        candidate.employment_type = ', '.join(emp_types)
        candidate.availability = ', '.join(availabilities)
        if commit:
            candidate.save()
            self.save_m2m()
        return candidate

    def clean_resume(self):
        return self._validate_pdf_only(self.cleaned_data.get('resume'), 'Resume')

    def clean_bgv_verification(self):
        return self._validate_pdf_only(self.cleaned_data.get('bgv_verification'), 'BGV Verification')

    def clean_evaluation_certificate(self):
        return self._validate_pdf_only(self.cleaned_data.get('evaluation_certificate'), 'Evaluation Certificate')
