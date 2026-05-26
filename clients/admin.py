from django.contrib import admin
from .models import Cart

class CartAdmin(admin.ModelAdmin):
    list_display = ('client', 'candidate', 'created_at')
    list_filter = ('client', 'candidate')
    search_fields = ('client__email', 'client__full_name', 'candidate__full_name')

admin.site.register(Cart, CartAdmin)
