from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('create/', views.candidate_create, name='candidate_create'),
    path('<int:pk>/edit/', views.candidate_update, name='candidate_edit'),
    path('<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('<int:pk>/toggle-hold/', views.candidate_toggle_hold, name='candidate_toggle_hold'),
    path('<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('admin-list/', views.admin_candidate_list, name='admin_candidate_list'),
    
    # Job Title routes
    path('job-titles/', views.job_title_list, name='job_title_list'),
    path('job-titles/create/', views.job_title_create, name='job_title_create'),
    path('job-titles/<int:pk>/edit/', views.job_title_update, name='job_title_edit'),
    path('job-titles/<int:pk>/delete/', views.job_title_delete, name='job_title_delete'),
    
    # Skill routes
    path('skills/', views.skill_list, name='skill_list'),
    path('skills/create/', views.skill_create, name='skill_create'),
    path('skills/<int:pk>/edit/', views.skill_update, name='skill_edit'),
    path('skills/<int:pk>/delete/', views.skill_delete, name='skill_delete'),
    
    # Credential requests routes
    path('<int:candidate_id>/request-credentials/', views.request_credentials, name='request_credentials'),
    path('requests/<int:request_id>/approve/', views.approve_credential_request, name='approve_credential_request'),
    path('requests/<int:request_id>/reject/', views.reject_credential_request, name='reject_credential_request'),
    path('<int:candidate_id>/document/<str:doc_type>/', views.download_candidate_document, name='download_candidate_document'),
]
