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

from accounts.decorators import admin_required
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
@admin_required
def admin_corporate_client_list(request):
    """List all Corporate Clients."""
    clients = CorporateClient.objects.select_related('user').prefetch_related('recruiter_assignments__recruiter')
    return render(request, 'myspace/admin/corporate_client_list.html', {'clients': clients})


@login_required
@admin_required
def admin_corporate_client_create(request):
    """Create a new Corporate Client account (User + Profile)."""
    if request.method == 'POST':
        user_form = CorporateClientUserForm(request.POST)
        profile_form = CorporateClientProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.role = 'corporate_client'
                user.company_name = profile_form.cleaned_data['company_name']
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            messages.success(request, f"Corporate Client '{profile.company_name}' created successfully.")
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
    """Edit an existing Corporate Client's user account and profile."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    if request.method == 'POST':
        user_form = CorporateClientEditUserForm(request.POST, instance=client_profile.user)
        profile_form = CorporateClientProfileForm(request.POST, instance=client_profile)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.company_name = profile_form.cleaned_data['company_name']
                user.save()
                profile_form.save()
            messages.success(request, f"Corporate Client '{client_profile.company_name}' updated successfully.")
            return redirect('admin_corporate_client_list')
    else:
        user_form = CorporateClientEditUserForm(instance=client_profile.user)
        profile_form = CorporateClientProfileForm(instance=client_profile)

    return render(request, 'myspace/admin/corporate_client_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'client_profile': client_profile,
        'title': 'Edit Corporate Client',
        'action': 'Save Changes',
    })


@login_required
@admin_required
def admin_corporate_client_toggle_active(request, pk):
    """Activate or deactivate a Corporate Client account."""
    client_profile = get_object_or_404(CorporateClient, pk=pk)
    client_profile.user.is_active = not client_profile.user.is_active
    client_profile.user.save()
    client_profile.is_active = client_profile.user.is_active
    client_profile.save()
    status = 'activated' if client_profile.user.is_active else 'deactivated'
    messages.success(request, f"Corporate Client '{client_profile.company_name}' has been {status}.")
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
@admin_required
def admin_job_overview(request):
    """Admin: view all job requirements across all corporate clients."""
    jobs = JobRequirement.objects.select_related('client', 'creator').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    return render(request, 'myspace/admin/job_overview.html', {
        'jobs': jobs,
        'status_filter': status_filter,
        'status_choices': JobRequirement.STATUS_CHOICES,
    })


@login_required
@admin_required
def admin_submission_overview(request):
    """Admin: view all candidate submissions."""
    submissions = CandidateSubmission.objects.select_related(
        'job__client', 'candidate', 'submitted_by'
    ).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    return render(request, 'myspace/admin/submission_overview.html', {
        'submissions': submissions,
        'status_filter': status_filter,
        'status_choices': CandidateSubmission.STATUS_CHOICES,
    })


@login_required
@admin_required
def admin_cart_overview(request):
    """Admin: view all corporate cart activity."""
    cart_items = CandidateCart.objects.select_related(
        'client', 'candidate', 'job'
    ).order_by('-created_at')
    return render(request, 'myspace/admin/cart_overview.html', {
        'cart_items': cart_items,
    })
