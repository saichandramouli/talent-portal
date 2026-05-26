from django import forms
from .models import Team, TechnologyStack

class TeamForm(forms.ModelForm):
    technology_stacks = forms.ModelMultipleChoiceField(
        queryset=TechnologyStack.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select tech stacks allowed for this team"
    )

    class Meta:
        model = Team
        fields = ['name', 'description', 'technology_stacks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Team'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Team Description'}),
        }

class TechnologyStackForm(forms.ModelForm):
    class Meta:
        model = TechnologyStack
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Django'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tech Stack Description'}),
        }
