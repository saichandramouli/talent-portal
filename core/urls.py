from django.urls import path
from .views import home_redirect_view

urlpatterns = [
    path('', home_redirect_view, name='home'),
]
