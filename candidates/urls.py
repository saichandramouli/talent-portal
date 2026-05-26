from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('create/', views.candidate_create, name='candidate_create'),
    path('<int:pk>/edit/', views.candidate_update, name='candidate_edit'),
    path('<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('admin-list/', views.admin_candidate_list, name='admin_candidate_list'),
]
