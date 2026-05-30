from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/mark-read/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
