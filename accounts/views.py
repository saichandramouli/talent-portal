from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import CustomLoginForm, RecruiterRegistrationForm, ClientRegistrationForm, RecruiterEditForm, AdminRecruiterCreationForm
from .decorators import admin_required
from teams.models import Team, TechnologyStack
from candidates.models import Candidate
from clients.models import Cart


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.full_name}!")
                    return redirect('home')
                else:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out successfully.")
    return redirect('login')

def register_recruiter(request):
    messages.error(request, "Self-registration for recruiters is disabled. Please contact an Administrator to set up your account.")
    return redirect('login')

def register_client(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = ClientRegistrationForm()
    return render(request, 'accounts/register_client.html', {'form': form})

@login_required
@admin_required
def admin_dashboard(request):
    # Stats
    total_recruiters = User.objects.filter(role='recruiter').count()
    total_clients = User.objects.filter(role='client').count()
    total_candidates = Candidate.objects.count()
    total_teams = Team.objects.count()
    total_stacks = TechnologyStack.objects.count()
    active_carts = Cart.objects.count()
    
    recent_candidates = Candidate.objects.order_by('-created_at')[:5]
    recruiters = User.objects.filter(role='recruiter').order_by('-created_at')
    clients = User.objects.filter(role='client').order_by('-created_at')
    
    context = {
        'total_recruiters': total_recruiters,
        'total_clients': total_clients,
        'total_candidates': total_candidates,
        'total_teams': total_teams,
        'total_stacks': total_stacks,
        'active_carts': active_carts,
        'recent_candidates': recent_candidates,
        'recruiters': recruiters,
        'clients': clients,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@login_required
@admin_required
def recruiter_list(request):
    recruiters = User.objects.filter(role='recruiter').order_by('-created_at')
    return render(request, 'accounts/recruiter_list.html', {'recruiters': recruiters})

@login_required
@admin_required
def client_list(request):
    clients = User.objects.filter(role='client').order_by('-created_at')
    return render(request, 'accounts/client_list.html', {'clients': clients})

@login_required
@admin_required
def edit_recruiter(request, pk):
    recruiter = get_object_or_404(User, pk=pk, role='recruiter')
    if request.method == 'POST':
        form = RecruiterEditForm(request.POST, instance=recruiter)
        if form.is_valid():
            form.save()
            messages.success(request, f"Recruiter {recruiter.full_name} updated successfully.")
            return redirect('recruiter_list')
    else:
        form = RecruiterEditForm(instance=recruiter)
    return render(request, 'accounts/user_edit.html', {'form': form, 'user_obj': recruiter})

@login_required
@admin_required
def toggle_recruiter_active(request, pk):
    recruiter = get_object_or_404(User, pk=pk, role='recruiter')
    recruiter.is_active = not recruiter.is_active
    recruiter.save()
    status = "activated" if recruiter.is_active else "deactivated"
    messages.success(request, f"Recruiter {recruiter.full_name} has been {status}.")
    
    referer = request.META.get('HTTP_REFERER', '')
    if 'admin-dashboard' in referer:
        return redirect('admin_dashboard')
    return redirect('recruiter_list')

@login_required
@admin_required
def toggle_client_active(request, pk):
    client = get_object_or_404(User, pk=pk, role='client')
    client.is_active = not client.is_active
    client.save()
    status = "activated" if client.is_active else "deactivated"
    messages.success(request, f"Client {client.full_name} has been {status}.")
    
    referer = request.META.get('HTTP_REFERER', '')
    if 'admin-dashboard' in referer:
        return redirect('admin_dashboard')
    return redirect('client_list')

@login_required
@admin_required
def create_recruiter(request):
    if request.method == 'POST':
        form = AdminRecruiterCreationForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            recruiter = form.save()
            
            # Send credentials email asynchronously using Celery
            try:
                from notifications.tasks import send_recruiter_creation_email_task
                send_recruiter_creation_email_task.delay(recruiter.id, password)
                messages.success(request, f"Recruiter account for {recruiter.full_name} created successfully. Credentials email sent.")
            except Exception as e:
                print(f"Celery task dispatch failed: {e}")
                messages.success(request, f"Recruiter account for {recruiter.full_name} created successfully. (Credentials email will be sent shortly).")
            return redirect('recruiter_list')
    else:
        form = AdminRecruiterCreationForm()
    return render(request, 'accounts/recruiter_create.html', {'form': form})
