from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from accounts.decorators import recruiter_required, role_required
from .models import Candidate, JobTitle, Skill, CredentialRequest
from .forms import CandidateForm, JobTitleForm, SkillForm
from teams.models import TechnologyStack

@login_required
@recruiter_required
def recruiter_dashboard(request):
    recruiter = request.user
    
    # Stats
    own_candidates = Candidate.objects.filter(recruiter=recruiter).prefetch_related('technical_stack', 'skills')
    total_own = own_candidates.count()
    
    if recruiter.team:
        allowed_stacks = recruiter.team.technology_stacks.all()
    else:
        allowed_stacks = TechnologyStack.objects.none()
        
    recent_uploads = own_candidates.order_by('-created_at')[:5]
    notifications = recruiter.notifications.all()
    
    # Fetch pending credential requests for this recruiter's candidates
    pending_requests = CredentialRequest.objects.filter(
        candidate__recruiter=recruiter,
        status='pending'
    ).select_related('client', 'candidate')
    
    context = {
        'total_own': total_own,
        'allowed_stacks': allowed_stacks,
        'recent_uploads': recent_uploads,
        'candidates': own_candidates,
        'notifications': notifications,
        'pending_requests': pending_requests,
    }
    return render(request, 'candidates/recruiter_dashboard.html', context)

@login_required
@recruiter_required
def candidate_create(request):
    recruiter = request.user
    if not recruiter.team:
        messages.error(request, "You must be assigned to a team by an Admin before you can upload candidates.")
        return redirect('recruiter_dashboard')

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, user=recruiter)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.recruiter = recruiter
            candidate.save()
            form.save_m2m() # Important for many-to-many fields
            messages.success(request, f"Candidate {candidate.full_name} uploaded successfully.")
            return redirect('recruiter_dashboard')
    else:
        form = CandidateForm(user=recruiter)
    return render(request, 'candidates/candidate_form.html', {'form': form, 'title': 'Add Candidate'})

@login_required
@role_required(['recruiter', 'admin'])
def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Ownership/Admin check
    if request.user.role == 'recruiter' and candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to edit this candidate.")
        return redirect('recruiter_dashboard')
        
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Candidate {candidate.full_name} updated successfully.")
            if request.user.role == 'admin':
                return redirect('admin_candidate_list')
            return redirect('recruiter_dashboard')
    else:
        form = CandidateForm(instance=candidate, user=request.user)
    return render(request, 'candidates/candidate_form.html', {'form': form, 'title': 'Edit Candidate', 'candidate': candidate})

@login_required
@role_required(['recruiter', 'admin'])
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Ownership/Admin check
    if request.user.role == 'recruiter' and candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to delete this candidate.")
        return redirect('recruiter_dashboard')
        
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, f"Candidate {candidate.full_name} deleted successfully.")
        if request.user.role == 'admin':
            return redirect('admin_candidate_list')
        return redirect('recruiter_dashboard')
    return render(request, 'candidates/candidate_confirm_delete.html', {'candidate': candidate})

@login_required
@role_required(['admin'])
def admin_candidate_list(request):
    candidates = Candidate.objects.all().select_related('recruiter', 'recruiter__team').prefetch_related('technical_stack', 'skills').order_by('-created_at')
    return render(request, 'admin/candidate_list.html', {'candidates': candidates})

@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Recruiter restriction check
    if request.user.role == 'recruiter':
        # Can only view if they are the owner, or if their team matches one of the candidate's stacks
        if candidate.recruiter != request.user:
            if not request.user.team:
                messages.error(request, "You are not authorized to view this candidate.")
                return redirect('recruiter_dashboard')
            # Check overlap between recruiter's team stacks and candidate's stacks
            recruiter_stacks = set(request.user.team.technology_stacks.all())
            candidate_stacks = set(candidate.technical_stack.all())
            if not recruiter_stacks.intersection(candidate_stacks):
                messages.error(request, "You are not authorized to view this candidate outside your team's stacks.")
                return redirect('recruiter_dashboard')
                
    # Client restriction check for candidates on hold
    if request.user.role == 'client' and candidate.is_on_hold:
        messages.error(request, "This candidate is currently on hold.")
        return redirect('client_dashboard')

    # Client has full read access to approved candidates (all candidates since approval is disabled)
    cart_candidate_ids = set()
    if request.user.role in ['client', 'corporate_client']:
        from clients.models import Cart
        cart_candidate_ids = set(Cart.objects.filter(client=request.user).values_list('candidate_id', flat=True))

    return render(request, 'candidates/candidate_detail.html', {
        'candidate': candidate,
        'cart_candidate_ids': cart_candidate_ids,
    })

@login_required
@role_required(['recruiter', 'admin'])
def candidate_toggle_hold(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Ownership/Admin check
    if request.user.role == 'recruiter' and candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to edit this candidate's hold status.")
        return redirect('recruiter_dashboard')
        
    if request.method == 'POST':
        candidate.is_on_hold = not candidate.is_on_hold
        candidate.save()
        status_str = "placed on hold" if candidate.is_on_hold else "removed from hold"
        messages.success(request, f"Candidate {candidate.full_name} has been {status_str}.")
        
    # Redirect back to referee or fallback
    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    if request.user.role == 'admin':
        return redirect('admin_candidate_list')
    return redirect('recruiter_dashboard')


# --- Job Title Admin Views ---

@login_required
@role_required(['admin'])
def job_title_list(request):
    job_titles = JobTitle.objects.all()
    return render(request, 'candidates/job_title_list.html', {'job_titles': job_titles})

@login_required
@role_required(['admin'])
def job_title_create(request):
    if request.method == 'POST':
        form = JobTitleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Job Title created successfully.")
            return redirect('job_title_list')
    else:
        form = JobTitleForm()
    return render(request, 'candidates/job_title_form.html', {'form': form, 'title': 'Add Job Title'})

@login_required
@role_required(['admin'])
def job_title_update(request, pk):
    job_title = get_object_or_404(JobTitle, pk=pk)
    if request.method == 'POST':
        form = JobTitleForm(request.POST, instance=job_title)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job Title '{job_title.name}' updated successfully.")
            return redirect('job_title_list')
    else:
        form = JobTitleForm(instance=job_title)
    return render(request, 'candidates/job_title_form.html', {'form': form, 'title': 'Edit Job Title', 'job_title': job_title})

@login_required
@role_required(['admin'])
def job_title_delete(request, pk):
    job_title = get_object_or_404(JobTitle, pk=pk)
    if request.method == 'POST':
        job_title.delete()
        messages.success(request, f"Job Title '{job_title.name}' deleted successfully.")
        return redirect('job_title_list')
    return render(request, 'candidates/job_title_confirm_delete.html', {'job_title': job_title})


# --- Skill Admin Views ---

@login_required
@role_required(['admin'])
def skill_list(request):
    skills = Skill.objects.all()
    return render(request, 'candidates/skill_list.html', {'skills': skills})

@login_required
@role_required(['admin'])
def skill_create(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Skill created successfully.")
            return redirect('skill_list')
    else:
        form = SkillForm()
    return render(request, 'candidates/skill_form.html', {'form': form, 'title': 'Add Skill'})

@login_required
@role_required(['admin'])
def skill_update(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, f"Skill '{skill.name}' updated successfully.")
            return redirect('skill_list')
    else:
        form = SkillForm(instance=skill)
    return render(request, 'candidates/skill_form.html', {'form': form, 'title': 'Edit Skill', 'skill': skill})

@login_required
@role_required(['admin'])
def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, f"Skill '{skill.name}' deleted successfully.")
        return redirect('skill_list')
    return render(request, 'candidates/skill_confirm_delete.html', {'skill': skill})


@login_required
@role_required(['client'])
def request_credentials(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if candidate.is_on_hold:
        messages.error(request, "This candidate is currently on hold.")
        return redirect('client_dashboard')
        
    req, created = CredentialRequest.objects.get_or_create(
        client=request.user,
        candidate=candidate
    )
    if created:
        messages.success(request, f"Credential request for {candidate.full_name} has been submitted successfully.")
    else:
        if req.status == 'rejected':
            req.status = 'pending'
            req.save()
            messages.success(request, f"Credential request for {candidate.full_name} has been re-submitted successfully.")
        else:
            messages.info(request, f"A credential request for {candidate.full_name} is already {req.status}.")
            
    return redirect('cart_view')


@login_required
@role_required(['recruiter', 'admin'])
def approve_credential_request(request, request_id):
    credential_request = get_object_or_404(CredentialRequest, id=request_id)
    if request.user.role == 'recruiter' and credential_request.candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to approve this request.")
        return redirect('recruiter_dashboard')
        
    credential_request.status = 'approved'
    credential_request.save()
    messages.success(request, f"Request from {credential_request.client.full_name} for candidate {credential_request.candidate.full_name} approved.")
    return redirect('recruiter_dashboard')


@login_required
@role_required(['recruiter', 'admin'])
def reject_credential_request(request, request_id):
    credential_request = get_object_or_404(CredentialRequest, id=request_id)
    if request.user.role == 'recruiter' and credential_request.candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to reject this request.")
        return redirect('recruiter_dashboard')
        
    credential_request.status = 'rejected'
    credential_request.save()
    messages.success(request, f"Request from {credential_request.client.full_name} for candidate {credential_request.candidate.full_name} rejected.")
    return redirect('recruiter_dashboard')


@login_required
def download_candidate_document(request, candidate_id, doc_type):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Access control: admin, authorized recruiter, or client with approved request
    has_access = False
    if request.user.role == 'admin':
        has_access = True
    elif request.user.role == 'recruiter':
        if candidate.recruiter == request.user:
            has_access = True
        elif request.user.team and request.user.team.technology_stacks.filter(id__in=candidate.technical_stack.all()).exists():
            has_access = True
    elif request.user.role == 'client':
        has_access = CredentialRequest.objects.filter(
            client=request.user,
            candidate=candidate,
            status='approved'
        ).exists()
        
    if not has_access:
        raise PermissionDenied("You do not have access to these credentials.")
        
    file_field = None
    if doc_type == 'resume':
        file_field = candidate.resume
    elif doc_type == 'bgv':
        file_field = candidate.bgv_verification
    elif doc_type == 'evaluation':
        file_field = candidate.evaluation_certificate
        
    if not file_field or not file_field.name:
        messages.error(request, f"No document uploaded for the {doc_type} of candidate {candidate.full_name}.")
        return redirect(request.META.get('HTTP_REFERER', 'client_dashboard'))
        
    # For remote storage (like Cloudinary), redirecting to the URL is the most reliable way to serve the file
    if hasattr(file_field, 'url') and file_field.url.startswith(('http://', 'https://')):
        return redirect(file_field.url)
        
    try:
        from django.http import FileResponse
        response = FileResponse(file_field.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{file_field.name.split("/")[-1]}"'
        return response
    except (OSError, ValueError):
        if hasattr(file_field, 'url'):
            return redirect(file_field.url)
        raise
