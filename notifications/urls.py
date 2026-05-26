from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.notification_logs, name='notification_logs'),
]
