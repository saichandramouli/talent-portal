from django.urls import path
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
    path('clients/', views.client_list, name='client_list'),
]
