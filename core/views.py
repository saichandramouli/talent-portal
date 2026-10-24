from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def home_redirect_view(request):
    """
    Redirects the user to their appropriate dashboard based on their role.
    """
    role = getattr(request.user, 'role', '')
    if getattr(request.user, 'is_superuser', False) or role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'recruiter':
        return redirect('recruiter_dashboard')
    elif role == 'client':
        return redirect('client_dashboard')
    elif role == 'corporate_client':
        return redirect('corporate_client_dashboard')
    elif role == 'manager':
        return redirect('manager_dashboard')
    elif role == 'ceo':
        return redirect('ceo_dashboard')
    else:
        # Default safe fallback: never redirect an authenticated user back to login (which causes redirect loop)
        if getattr(request.user, 'is_staff', False):
            return redirect('admin_dashboard')
        return redirect('client_dashboard')

