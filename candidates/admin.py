from django.contrib import admin
from .models import Candidate, CredentialRequest

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'years_of_experience', 'rate_card', 'location', 'availability', 'recruiter', 'created_at')
    list_filter = ('location', 'availability', 'recruiter')
    filter_horizontal = ('technical_stack',)
    search_fields = ('full_name', 'location', 'summary')

class CredentialRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'candidate', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'client', 'candidate')

admin.site.register(Candidate, CandidateAdmin)
admin.site.register(CredentialRequest, CredentialRequestAdmin)
