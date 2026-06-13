from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks if the logged-in user belongs to any of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('login')
            
            # Admins have full access to everything, so bypass role restriction if role is 'admin' or user is superuser
            if request.user.role == 'admin' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You are not authorized to view this page.")
            # Redirect to home, which will redirect them to their respective dashboard
            return redirect('home')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def recruiter_required(view_func):
    return role_required(['recruiter'])(view_func)

def client_required(view_func):
    return role_required(['client'])(view_func)

def corporate_client_required(view_func):
    return role_required(['corporate_client'])(view_func)
