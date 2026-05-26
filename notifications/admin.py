from django.contrib import admin
from .models import NotificationLog

class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('email_sent_to', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email_sent_to', 'subject', 'message')
    readonly_fields = ('client', 'candidate', 'email_sent_to', 'subject', 'message', 'status', 'created_at')

admin.site.register(NotificationLog, NotificationLogAdmin)
