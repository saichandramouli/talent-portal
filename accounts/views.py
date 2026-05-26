from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import CustomLoginForm, RecruiterRegistrationForm, ClientRegistrationForm, RecruiterEditForm
from .decorators import admin_required
from teams.models import Team, TechnologyStack
from candidates.models import Candidate
from clients.models import Cart
from notifications.models import NotificationLog

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
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RecruiterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You can now log in. Note: Admin needs to assign you a Team.")
            return redirect('login')
    else:
        form = RecruiterRegistrationForm()
    return render(request, 'accounts/register_recruiter.html', {'form': form})

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
    recent_logs = NotificationLog.objects.order_by('-created_at')[:5]
    
    context = {
        'total_recruiters': total_recruiters,
        'total_clients': total_clients,
        'total_candidates': total_candidates,
        'total_teams': total_teams,
        'total_stacks': total_stacks,
        'active_carts': active_carts,
        'recent_candidates': recent_candidates,
        'recent_logs': recent_logs,
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
    return redirect('recruiter_list')
