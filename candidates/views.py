from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from accounts.decorators import recruiter_required, role_required
from .models import Candidate
from .forms import CandidateForm
from teams.models import TechnologyStack

@login_required
@recruiter_required
def recruiter_dashboard(request):
    recruiter = request.user
    
    # Stats
    own_candidates = Candidate.objects.filter(recruiter=recruiter)
    total_own = own_candidates.count()
    
    if recruiter.team:
        allowed_stacks = recruiter.team.technology_stacks.all()
    else:
        allowed_stacks = TechnologyStack.objects.none()
        
    recent_uploads = own_candidates.order_by('-created_at')[:5]
    
    context = {
        'total_own': total_own,
        'allowed_stacks': allowed_stacks,
        'recent_uploads': recent_uploads,
        'candidates': own_candidates,
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
    candidates = Candidate.objects.all().order_by('-created_at')
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
                
    # Client has full read access to approved candidates (all candidates since approval is disabled)
    return render(request, 'candidates/candidate_detail.html', {'candidate': candidate})
