from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def home_redirect_view(request):
    """
    Redirects the user to their appropriate dashboard based on their role.
    """
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'recruiter':
        return redirect('recruiter_dashboard')
    elif request.user.role == 'client':
        return redirect('client_dashboard')
    else:
        # Default fallback
        return redirect('login')
