from django.contrib import admin
from .models import Candidate

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'years_of_experience', 'rate_card', 'location', 'availability', 'recruiter', 'created_at')
    list_filter = ('location', 'availability', 'recruiter')
    filter_horizontal = ('technical_stack',)
    search_fields = ('full_name', 'location', 'summary')

admin.site.register(Candidate, CandidateAdmin)
