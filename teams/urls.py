from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.team_create, name='team_create'),
    path('<int:pk>/edit/', views.team_update, name='team_edit'),
    path('<int:pk>/delete/', views.team_delete, name='team_delete'),
    
    path('stacks/', views.stack_list, name='stack_list'),
    path('stacks/create/', views.stack_create, name='stack_create'),
    path('stacks/<int:pk>/edit/', views.stack_update, name='stack_edit'),
    path('stacks/<int:pk>/delete/', views.stack_delete, name='stack_delete'),
]
