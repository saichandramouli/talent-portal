from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required
from .models import NotificationLog

@login_required
@admin_required
def notification_logs(request):
    logs = NotificationLog.objects.all().order_by('-created_at')
    return render(request, 'admin/notification_logs.html', {'logs': logs})
