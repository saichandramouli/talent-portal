from django.contrib import admin
from .models import Team, TechnologyStack

class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    filter_horizontal = ('technology_stacks',)
    search_fields = ('name',)

class TechnologyStackAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

admin.site.register(Team, TeamAdmin)
admin.site.register(TechnologyStack, TechnologyStackAdmin)
