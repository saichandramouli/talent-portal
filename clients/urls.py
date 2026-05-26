from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:candidate_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:candidate_id>/', views.remove_from_cart, name='remove_from_cart'),
]
