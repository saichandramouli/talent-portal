"""
Admin views for the My Space module.
All views here are protected by @admin_required.
Admins can create/edit/activate/deactivate Corporate Clients,
manage recruiter assignments, and view all jobs and submissions.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from accounts.decorators import admin_required, admin_or_ceo_required
from accounts.models import User
from myspace.models import (
    CorporateClient, RecruiterClientAssignment,
    JobRequirement, CandidateSubmission, CandidateCart
)
from myspace.forms import (
    CorporateClientUserForm, CorporateClientProfileForm,
    CorporateClientEditUserForm, RecruiterAssignmentForm
)


@login_required
@admin_or_ceo_required
def admin_corporate_client_list(request):
    """List all Corporate Clients."""
    clients = CorporateClient.objects.prefetch_related('users', 'recruiter_assignments__recruiter')
    return render(request, 'myspace/admin/corporate_client_list.html', {'clients': clients})

@login_required
@admin_or_ceo_required
def admin_corporate_client_detail(request, pk):
    """View detailed information about a Corporate Client."""
    client = get_object_or_404(CorporateClient, pk=pk)
    
    context = {
        'client_profile': client,
        'users': client.users.all(),
        'jobs': client.job_requirements.all().order_by('-created_at'),
        'recruiter_assignments': client.recruiter_assignments.select_related('recruiter').all(),
    }
    return render(request, 'myspace/admin/corporate_client_detail.html', context)

@login_required
@admin_required
def admin_corporate_client_create(request):
    """Create a new Corporate Client account (User + Profile)."""
    if request.method == 'POST':
        user_form = CorporateClientUserForm(request.POST)
        profile_form = CorporateClientProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                profile = profile_form.save()
                user = user_form.save(commit=False)
                user.role = 'corporate_client'
                user.company_name = profile.company_name
                user.corporate_client = profile
                user.set_password(user_form.cleaned_data['password'])
                user.save()
            messages.success(request, f"Corporate Client '{profile.company_name}' and primary user created successfully.")
            return redirect('admin_corporate_client_list')
    else:
        user_form = CorporateClientUserForm()
        profile_form = CorporateClientProfileForm()

    return render(request, 'myspace/admin/corporate_client_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Create Corporate Client',
        'action': 'Create',
    })


@login_required
@admin_required
def admin_corporate_client_edit(request, pk):
    """Edit an existing Corporate Client's profile."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    if request.method == 'POST':
        profile_form = CorporateClientProfileForm(request.POST, instance=client_profile)
        if profile_form.is_valid():
            profile_form.save()
            # Sync company name with all associated users
            client_profile.users.update(company_name=client_profile.company_name)
            messages.success(request, f"Corporate Client '{client_profile.company_name}' updated successfully.")
            return redirect('admin_corporate_client_list')
    else:
        profile_form = CorporateClientProfileForm(instance=client_profile)

    return render(request, 'myspace/admin/corporate_client_form.html', {
        'profile_form': profile_form,
        'client_profile': client_profile,
        'title': 'Edit Corporate Client',
        'action': 'Save Changes',
    })


@login_required
@admin_required
def admin_corporate_client_toggle_active(request, pk):
    """Activate or deactivate a Corporate Client profile and all associated users."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    client_profile.is_active = not client_profile.is_active
    client_profile.save()
    
    # Toggle active status on all users of this client
    client_profile.users.update(is_active=client_profile.is_active)
    
    status = 'activated' if client_profile.is_active else 'deactivated'
    messages.success(request, f"Corporate Client '{client_profile.company_name}' and all associated users have been {status}.")
    return redirect('admin_corporate_client_list')


@login_required
@admin_required
def admin_assign_recruiters(request, pk):
    """Assign/un-assign recruiters to a Corporate Client."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    current_recruiter_ids = list(
        RecruiterClientAssignment.objects.filter(client=client_profile).values_list('recruiter_id', flat=True)
    )

    if request.method == 'POST':
        form = RecruiterAssignmentForm(request.POST)
        if form.is_valid():
            selected_recruiters = form.cleaned_data['recruiters']
            selected_ids = [r.id for r in selected_recruiters]

            with transaction.atomic():
                # Remove unselected
                RecruiterClientAssignment.objects.filter(
                    client=client_profile
                ).exclude(recruiter_id__in=selected_ids).delete()

                # Add newly selected
                for recruiter in selected_recruiters:
                    RecruiterClientAssignment.objects.get_or_create(
                        client=client_profile,
                        recruiter=recruiter
                    )

            messages.success(request, f"Recruiter assignments for '{client_profile.company_name}' updated.")
            return redirect('admin_corporate_client_list')
    else:
        form = RecruiterAssignmentForm(initial={'recruiters': current_recruiter_ids})

    return render(request, 'myspace/admin/assign_recruiters.html', {
        'form': form,
        'client_profile': client_profile,
        'current_recruiter_ids': current_recruiter_ids,
    })


@login_required
@admin_or_ceo_required
def admin_job_overview(request):
    """Admin: view all job requirements across all corporate clients."""
    jobs = JobRequirement.objects.select_related('client', 'creator').order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
        
    client_filter = request.GET.get('client_id', '')
    if client_filter:
        jobs = jobs.filter(client_id=client_filter)
        
    corporate_clients = CorporateClient.objects.all().order_by('company_name')
        
    return render(request, 'myspace/admin/job_overview.html', {
        'jobs': jobs,
        'status_filter': status_filter,
        'client_filter': client_filter,
        'status_choices': JobRequirement.STATUS_CHOICES,
        'corporate_clients': corporate_clients,
    })


@login_required
@admin_or_ceo_required
def admin_submission_overview(request):
    """Admin: view all candidate submissions."""
    submissions = CandidateSubmission.objects.select_related(
        'job__client', 'candidate', 'submitted_by'
    ).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
        
    client_filter = request.GET.get('client_id', '')
    if client_filter:
        submissions = submissions.filter(job__client_id=client_filter)
        
    corporate_clients = CorporateClient.objects.all().order_by('company_name')
        
    return render(request, 'myspace/admin/submission_overview.html', {
        'submissions': submissions,
        'status_filter': status_filter,
        'client_filter': client_filter,
        'status_choices': CandidateSubmission.STATUS_CHOICES,
        'corporate_clients': corporate_clients,
    })


@login_required
@admin_or_ceo_required
def admin_cart_overview(request):
    """Admin: view all corporate cart activity."""
    cart_items = CandidateCart.objects.select_related(
        'user', 'user__corporate_client', 'candidate', 'job'
    ).order_by('-created_at')
    return render(request, 'myspace/admin/cart_overview.html', {
        'cart_items': cart_items,
    })


@login_required
@admin_required
def admin_job_delete(request, job_pk):
    """Allow Admin to delete any Job Requirement."""
    job = get_object_or_404(JobRequirement, pk=job_pk)
    if request.method == 'POST':
        title = job.job_title
        job.delete()
        messages.success(request, f"Job requirement '{title}' has been successfully deleted.")
        return redirect('admin_myspace_job_overview')
    return render(request, 'myspace/admin/job_confirm_delete.html', {
        'job': job,
    })


@login_required
@admin_required
def admin_submission_delete(request, submission_pk):
    """Allow Admin to delete any Candidate Submission."""
    submission = get_object_or_404(CandidateSubmission, pk=submission_pk)
    if request.method == 'POST':
        candidate_name = submission.candidate.full_name
        job_title = submission.job.job_title
        submission.delete()
        messages.success(request, f"Submission of '{candidate_name}' for job '{job_title}' has been successfully deleted.")
        return redirect('admin_myspace_submission_overview')
    return render(request, 'myspace/admin/submission_confirm_delete.html', {
        'submission': submission,
    })


@login_required
@admin_required
def admin_corporate_client_delete(request, pk):
    """Delete Corporate Client company and all associated users."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    company_name = client_profile.company_name
    with transaction.atomic():
        client_profile.users.all().delete()
        client_profile.delete()
    messages.success(request, f"Corporate Client '{company_name}' and all its users have been permanently deleted.")
    return redirect('admin_corporate_client_list')


@login_required
@admin_required
def admin_corporate_client_users(request, client_pk):
    """List all user login accounts for a specific Corporate Client."""
    client_profile = get_object_or_404(CorporateClient, pk=client_pk)
    users = client_profile.users.all().order_by('-created_at')
    return render(request, 'myspace/admin/corporate_client_users.html', {
        'client_profile': client_profile,
        'users': users,
    })


@login_required
@admin_required
def admin_corporate_client_user_create(request, client_pk):
    """Create a new user login for a Corporate Client."""
    client_profile = get_object_or_404(CorporateClient, pk=client_pk)
    if request.method == 'POST':
        form = CorporateClientUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'corporate_client'
            user.company_name = client_profile.company_name
            user.corporate_client = client_profile
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"User account for '{user.full_name}' created successfully.")
            return redirect('admin_corporate_client_users', client_pk=client_pk)
    else:
        form = CorporateClientUserForm()
        
    return render(request, 'myspace/admin/corporate_client_user_form.html', {
        'form': form,
        'client_profile': client_profile,
        'title': f"Add User to {client_profile.company_name}",
        'action': 'Add User',
    })


@login_required
@admin_required
def admin_corporate_client_user_edit(request, client_pk, user_pk):
    """Edit an existing user login for a Corporate Client."""
    client_profile = get_object_or_404(CorporateClient, pk=client_pk)
    user = get_object_or_404(User, pk=user_pk, corporate_client=client_profile)
    if request.method == 'POST':
        form = CorporateClientEditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User account for '{user.full_name}' updated.")
            return redirect('admin_corporate_client_users', client_pk=client_pk)
    else:
        form = CorporateClientEditUserForm(instance=user)
        
    return render(request, 'myspace/admin/corporate_client_user_form.html', {
        'form': form,
        'client_profile': client_profile,
        'user_obj': user,
        'title': f"Edit User '{user.full_name}'",
        'action': 'Save Changes',
    })


@login_required
@admin_required
def admin_corporate_client_user_toggle_active(request, client_pk, user_pk):
    """Toggle a user's active status."""
    client_profile = get_object_or_404(CorporateClient, pk=client_pk)
    user = get_object_or_404(User, pk=user_pk, corporate_client=client_profile)
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f"User '{user.full_name}' has been {status}.")
    return redirect('admin_corporate_client_users', client_pk=client_pk)

