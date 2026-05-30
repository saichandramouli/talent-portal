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
    class Meta:
        model = Candidate
        fields = [
            'profile_photo', 'full_name', 'job_title', 'skills', 'years_of_experience',
            'rate_card', 'technical_stack', 'location', 'availability', 'is_on_hold'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Candidate Full Name'}),
            'job_title': forms.Select(attrs={'class': 'form-select'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g. 5'}),
            'rate_card': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.00'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New York, NY'}),
            'availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Immediate, 2 Weeks'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_on_hold': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'technical_stack': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
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
