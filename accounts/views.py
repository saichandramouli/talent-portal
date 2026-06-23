from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import CustomLoginForm, RecruiterRegistrationForm, ClientRegistrationForm, RecruiterEditForm, AdminRecruiterCreationForm, AdminManagerCreationForm, ManagerEditForm, ClientEditForm
from .decorators import admin_required, admin_or_ceo_required
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
    total_managers = User.objects.filter(role='manager').count()
    total_clients = User.objects.filter(role='client').count()
    total_candidates = Candidate.objects.count()
    total_teams = Team.objects.count()
    total_stacks = TechnologyStack.objects.count()
    active_carts = Cart.objects.count()
    
    recent_candidates = Candidate.objects.select_related('recruiter').order_by('-created_at')[:5]
    recruiters = User.objects.filter(role='recruiter').order_by('-created_at')
    clients = User.objects.filter(role='client').order_by('-created_at')
    
    context = {
        'total_recruiters': total_recruiters,
        'total_managers': total_managers,
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
@admin_or_ceo_required
def recruiter_list(request):
    recruiters = User.objects.filter(role='recruiter').order_by('-created_at')
    return render(request, 'accounts/recruiter_list.html', {'recruiters': recruiters})

@login_required
@admin_or_ceo_required
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
def edit_client(request, pk):
    client = get_object_or_404(User, pk=pk, role='client')
    if request.method == 'POST':
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client {client.full_name} updated successfully.")
            return redirect('client_list')
    else:
        form = ClientEditForm(instance=client)
    return render(request, 'accounts/user_edit.html', {'form': form, 'user_obj': client, 'is_client': True})


@login_required
@admin_required
def delete_client(request, pk):
    client = get_object_or_404(User, pk=pk, is_active=False)
    if client.role not in ['client', 'corporate_client']:
        messages.error(request, "Only deactivated client or corporate client accounts can be deleted.")
        return redirect('client_list')
    
    role = client.role
    client_name = client.full_name
    client.delete()
    messages.success(request, f"Client {client_name} has been deleted successfully.")
    if role == 'corporate_client':
        return redirect('admin_corporate_client_list')
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

@login_required
@admin_or_ceo_required
def manager_list(request):
    managers = User.objects.filter(role='manager').order_by('-created_at')
    return render(request, 'accounts/manager_list.html', {'managers': managers})

@login_required
@admin_required
def create_manager(request):
    if request.method == 'POST':
        form = AdminManagerCreationForm(request.POST)
        if form.is_valid():
            manager_obj = form.save()
            messages.success(request, f"Manager account for {manager_obj.full_name} created successfully.")
            return redirect('manager_list')
    else:
        form = AdminManagerCreationForm()
    return render(request, 'accounts/manager_create.html', {'form': form})

@login_required
@admin_required
def edit_manager(request, pk):
    manager_obj = get_object_or_404(User, pk=pk, role='manager')
    if request.method == 'POST':
        form = ManagerEditForm(request.POST, instance=manager_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Manager {manager_obj.full_name} updated successfully.")
            return redirect('manager_list')
    else:
        form = ManagerEditForm(instance=manager_obj)
    return render(request, 'accounts/user_edit.html', {'form': form, 'user_obj': manager_obj, 'is_manager': True})

@login_required
@admin_required
def toggle_manager_active(request, pk):
    manager_obj = get_object_or_404(User, pk=pk, role='manager')
    manager_obj.is_active = not manager_obj.is_active
    manager_obj.save()
    status = "activated" if manager_obj.is_active else "deactivated"
    messages.success(request, f"Manager {manager_obj.full_name} has been {status}.")
    return redirect('manager_list')
