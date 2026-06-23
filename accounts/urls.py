from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/recruiter/', views.register_recruiter, name='register_recruiter'),
    path('register/client/', views.register_client, name='register_client'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('recruiters/', views.recruiter_list, name='recruiter_list'),
    path('recruiters/create/', views.create_recruiter, name='create_recruiter'),
    path('recruiters/<int:pk>/edit/', views.edit_recruiter, name='edit_recruiter'),
    path('recruiters/<int:pk>/toggle-active/', views.toggle_recruiter_active, name='toggle_recruiter_active'),
    path('managers/', views.manager_list, name='manager_list'),
    path('managers/create/', views.create_manager, name='create_manager'),
    path('managers/<int:pk>/edit/', views.edit_manager, name='edit_manager'),
    path('managers/<int:pk>/toggle-active/', views.toggle_manager_active, name='toggle_manager_active'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:pk>/edit/', views.edit_client, name='edit_client'),
    path('clients/<int:pk>/delete/', views.delete_client, name='delete_client'),
    path('clients/<int:pk>/toggle-active/', views.toggle_client_active, name='toggle_client_active'),



    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]
