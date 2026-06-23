"""
Recruiter views for the My Space module.
Recruiters see only their assigned Corporate Clients.
They manage CorporateCandidates, JobRequirements, and Submissions.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import recruiter_required
from myspace.models import (
    CorporateClient, RecruiterClientAssignment, CorporateCandidate,
    JobRequirement, CandidateSubmission, SubmissionStatusHistory,
    CorporateCredentialRequest
)
from myspace.forms import (
    JobRequirementForm, CorporateCandidateForm,
    CandidateSubmissionForm, SubmissionStatusForm
)


def _get_assigned_client_or_404(recruiter, client_pk):
    """Ensure the recruiter is assigned to this client; otherwise 404."""
    get_object_or_404(RecruiterClientAssignment, recruiter=recruiter, client_id=client_pk)
    return get_object_or_404(CorporateClient, pk=client_pk)


# ─── My Space Home ─────────────────────────────────────────────────────────────

@login_required
@recruiter_required
def recruiter_my_space(request):
    """My Space landing: list of Corporate Clients assigned to this recruiter."""
    assignments = RecruiterClientAssignment.objects.filter(
        recruiter=request.user
    ).select_related('client')
    clients = [a.client for a in assignments]
    
    pending_requests = CorporateCredentialRequest.objects.filter(
        candidate__recruiter=request.user,
        status='pending'
    ).select_related('client', 'candidate')

    return render(request, 'myspace/recruiter/my_space.html', {
        'clients': clients,
        'pending_requests': pending_requests,
    })


# ─── Jobs ─────────────────────────────────────────────────────────────────────

@login_required
@recruiter_required
def recruiter_job_list(request, client_pk):
    """List all jobs for a given Corporate Client (only if recruiter is assigned)."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    jobs = JobRequirement.objects.filter(client=client, creator=request.user).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    return render(request, 'myspace/recruiter/job_list.html', {
        'client': client,
        'jobs': jobs,
        'status_filter': status_filter,
        'status_choices': JobRequirement.STATUS_CHOICES,
    })


@login_required
@recruiter_required
def recruiter_job_create(request, client_pk):
    """Create a new Job Requirement for this Corporate Client."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    if request.method == 'POST':
        form = JobRequirementForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = client
            job.creator = request.user
            job.save()
            messages.success(request, f"Job '{job.job_title}' created successfully.")
            return redirect('recruiter_job_list', client_pk=client_pk)
    else:
        form = JobRequirementForm()
    return render(request, 'myspace/recruiter/job_form.html', {
        'form': form,
        'client': client,
        'title': 'Create Job Requirement',
        'action': 'Create',
    })


@login_required
@recruiter_required
def recruiter_job_edit(request, client_pk, job_pk):
    """Edit an existing Job Requirement."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=client, creator=request.user)
    if request.method == 'POST':
        form = JobRequirementForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.job_title}' updated.")
            return redirect('recruiter_job_list', client_pk=client_pk)
    else:
        form = JobRequirementForm(instance=job)
    return render(request, 'myspace/recruiter/job_form.html', {
        'form': form,
        'client': client,
        'job': job,
        'title': 'Edit Job Requirement',
        'action': 'Save Changes',
    })


@login_required
@recruiter_required
def recruiter_job_detail(request, client_pk, job_pk):
    """View a job's details along with all submitted candidates."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=client, creator=request.user)
    submissions = job.submissions.select_related('candidate').order_by('-created_at')
    return render(request, 'myspace/recruiter/job_detail.html', {
        'client': client,
        'job': job,
        'submissions': submissions,
    })


@login_required
@recruiter_required
def recruiter_job_delete(request, client_pk, job_pk):
    """Delete a Job Requirement."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=client, creator=request.user)
    if request.method == 'POST':
        title = job.job_title
        job.delete()
        messages.success(request, f"Job '{title}' deleted.")
        return redirect('recruiter_job_list', client_pk=client_pk)
    return render(request, 'myspace/recruiter/job_confirm_delete.html', {
        'client': client,
        'job': job,
    })


# ─── Corporate Candidates ─────────────────────────────────────────────────────

@login_required
@recruiter_required
def recruiter_candidate_list(request):
    """All Corporate Candidates uploaded by this recruiter."""
    candidates = CorporateCandidate.objects.filter(recruiter=request.user)
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    if q:
        candidates = candidates.filter(full_name__icontains=q) | candidates.filter(technology_stack__icontains=q)
        candidates = candidates.distinct()
    if status_filter:
        candidates = candidates.filter(status=status_filter)
    return render(request, 'myspace/recruiter/candidate_list.html', {
        'candidates': candidates,
        'q': q,
        'status_filter': status_filter,
        'status_choices': CorporateCandidate.STATUS_CHOICES,
    })


@login_required
@recruiter_required
def recruiter_candidate_create(request):
    """Add a new Corporate Candidate."""
    if request.method == 'POST':
        form = CorporateCandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.recruiter = request.user
            candidate.save()
            messages.success(request, f"Candidate '{candidate.full_name}' added to My Space.")
            return redirect('recruiter_corporate_candidate_list')
    else:
        form = CorporateCandidateForm()
    return render(request, 'myspace/recruiter/candidate_form.html', {
        'form': form,
        'title': 'Add Corporate Candidate',
        'action': 'Add Candidate',
    })


@login_required
@recruiter_required
def recruiter_candidate_edit(request, candidate_pk):
    """Edit a Corporate Candidate (only own candidates)."""
    candidate = get_object_or_404(CorporateCandidate, pk=candidate_pk, recruiter=request.user)
    if request.method == 'POST':
        form = CorporateCandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f"Candidate '{candidate.full_name}' updated.")
            return redirect('recruiter_corporate_candidate_list')
    else:
        form = CorporateCandidateForm(instance=candidate)
    return render(request, 'myspace/recruiter/candidate_form.html', {
        'form': form,
        'candidate': candidate,
        'title': 'Edit Corporate Candidate',
        'action': 'Save Changes',
    })


@login_required
@recruiter_required
def recruiter_candidate_delete(request, candidate_pk):
    """Delete a Corporate Candidate (only own candidates)."""
    candidate = get_object_or_404(CorporateCandidate, pk=candidate_pk, recruiter=request.user)
    if request.method == 'POST':
        name = candidate.full_name
        candidate.delete()
        messages.success(request, f"Candidate '{name}' deleted.")
        return redirect('recruiter_corporate_candidate_list')
    return render(request, 'myspace/recruiter/candidate_confirm_delete.html', {'candidate': candidate})


# ─── Submissions ──────────────────────────────────────────────────────────────

@login_required
@recruiter_required
def recruiter_submit_candidates(request, client_pk, job_pk):
    """Submit one or more Corporate Candidates to a Job Requirement."""
    client = _get_assigned_client_or_404(request.user, client_pk)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=client, creator=request.user)

    # Already submitted candidates for this job
    already_submitted_ids = list(
        CandidateSubmission.objects.filter(job=job).values_list('candidate_id', flat=True)
    )

    if request.method == 'POST':
        form = CandidateSubmissionForm(
            request.POST,
            recruiter=request.user,
            exclude_ids=already_submitted_ids
        )
        if form.is_valid():
            candidates = form.cleaned_data['candidates']
            for cand in candidates:
                sub = CandidateSubmission.objects.create(
                    job=job,
                    candidate=cand,
                    submitted_by=request.user,
                    status='submitted'
                )
                SubmissionStatusHistory.objects.create(
                    submission=sub,
                    status='submitted',
                    changed_by=request.user,
                    comments='Initial submission'
                )
            messages.success(request, f"{len(candidates)} candidate(s) submitted to '{job.job_title}'.")
            return redirect('recruiter_job_detail', client_pk=client_pk, job_pk=job_pk)
    else:
        form = CandidateSubmissionForm(recruiter=request.user, exclude_ids=already_submitted_ids)

    return render(request, 'myspace/recruiter/submission_form.html', {
        'form': form,
        'client': client,
        'job': job,
    })


@login_required
@recruiter_required
def recruiter_update_submission_status(request, submission_pk):
    """Update the status of a candidate submission."""
    submission = get_object_or_404(CandidateSubmission, pk=submission_pk, submitted_by=request.user)
    if request.method == 'POST':
        form = SubmissionStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            comments = form.cleaned_data.get('comments', '')
            old_status = submission.status
            submission.status = new_status
            submission.save()
            SubmissionStatusHistory.objects.create(
                submission=submission,
                status=new_status,
                changed_by=request.user,
                comments=comments
            )
            messages.success(request, f"Submission status updated from '{old_status}' to '{new_status}'.")
            return redirect('recruiter_job_detail',
                            client_pk=submission.job.client_id,
                            job_pk=submission.job_id)
    else:
        form = SubmissionStatusForm(initial={'status': submission.status})
    return render(request, 'myspace/recruiter/update_status_form.html', {
        'form': form,
        'submission': submission,
    })


@login_required
@recruiter_required
def approve_corporate_credential_request(request, request_id):
    credential_request = get_object_or_404(CorporateCredentialRequest, id=request_id)
    if credential_request.candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to approve this request.")
        return redirect('recruiter_my_space')
        
    credential_request.status = 'approved'
    credential_request.save()
    messages.success(request, f"Request from {credential_request.client.company_name} for candidate {credential_request.candidate.full_name} approved.")
    return redirect('recruiter_my_space')


@login_required
@recruiter_required
def reject_corporate_credential_request(request, request_id):
    credential_request = get_object_or_404(CorporateCredentialRequest, id=request_id)
    if credential_request.candidate.recruiter != request.user:
        messages.error(request, "You are not authorized to reject this request.")
        return redirect('recruiter_my_space')
        
    credential_request.status = 'rejected'
    credential_request.save()
    messages.success(request, f"Request from {credential_request.client.company_name} for candidate {credential_request.candidate.full_name} rejected.")
    return redirect('recruiter_my_space')

