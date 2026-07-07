"""
Corporate Client views for the My Space module.
All views here are protected by @corporate_client_required.
Corporate Clients see ONLY their own jobs, only candidates submitted to their jobs,
and can manage their shortlist cart.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import corporate_client_required
from myspace.models import (
    CorporateClient, JobRequirement, CandidateSubmission,
    SubmissionStatusHistory, CandidateCart, CorporateCandidate,
    CorporateCredentialRequest
)
from myspace.forms import SubmissionStatusForm


def _get_corporate_client(user):
    """Return CorporateClient profile for the logged-in user."""
    return get_object_or_404(CorporateClient, user=user)


from django.db.models import Count, Q
from myspace.forms import CorporateClientJobRequirementForm


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
@corporate_client_required
def corporate_client_dashboard(request):
    """Corporate Client main dashboard."""
    corp = _get_corporate_client(request.user)
    
    # Simple dashboard stats
    jobs = JobRequirement.objects.filter(client=corp)
    total_jobs = jobs.count()
    open_jobs = jobs.filter(status='open').count()
    total_submissions = CandidateSubmission.objects.filter(job__client=corp).count()
    cart_count = CandidateCart.objects.filter(client=corp).count()
    
    recent_submissions = CandidateSubmission.objects.filter(
        job__client=corp
    ).select_related('candidate', 'job').order_by('-created_at')[:5]

    return render(request, 'myspace/client/dashboard.html', {
        'corp': corp,
        'total_jobs': total_jobs,
        'open_jobs': open_jobs,
        'total_submissions': total_submissions,
        'cart_count': cart_count,
        'recent_submissions': recent_submissions,
    })


@login_required
@corporate_client_required
def corporate_client_jobs_posted(request):
    """List only the jobs posted by the Corporate Client themselves (not recruiters) in a tracker table."""
    corp = _get_corporate_client(request.user)
    
    # Filter jobs created/added by the corporate client user themselves
    jobs = JobRequirement.objects.filter(client=corp, creator=request.user).annotate(
        submission_count=Count('submissions'),
        shortlist_count=Count('submissions', filter=Q(submissions__status='shortlisted')),
        interview_count=Count('submissions', filter=Q(submissions__status='interview_scheduled')),
        select_yet_to_offer_count=Count('submissions', filter=Q(submissions__status='selected_yet_to_offer')),
        offered_yet_to_join_count=Count('submissions', filter=Q(submissions__status='offered_yet_to_join')),
        joined_count=Count('submissions', filter=Q(submissions__status='joined'))
    ).order_by('-created_at')

    # Calculate sums for footer
    totals = {
        'num_positions': sum(j.num_positions for j in jobs),
        'submissions': sum(j.submission_count for j in jobs),
        'shortlisted': sum(j.shortlist_count for j in jobs),
        'interviews': sum(j.interview_count for j in jobs),
        'select_yet_to_offer': sum(j.select_yet_to_offer_count for j in jobs),
        'offered_yet_to_join': sum(j.offered_yet_to_join_count for j in jobs),
        'joined': sum(j.joined_count for j in jobs),
    }

    return render(request, 'myspace/client/client_jobs.html', {
        'corp': corp,
        'jobs': jobs,
        'totals': totals,
    })


@login_required
@corporate_client_required
def corporate_client_job_create(request):
    """Allow Corporate Client to create a Job Posting."""
    corp = _get_corporate_client(request.user)
    if request.method == 'POST':
        form = CorporateClientJobRequirementForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = corp
            job.creator = request.user
            job.save()
            messages.success(request, f"Job requirement '{job.job_title}' posted successfully.")
            return redirect('corporate_client_dashboard')
    else:
        form = CorporateClientJobRequirementForm()
    return render(request, 'myspace/client/job_form.html', {
        'form': form,
        'corp': corp,
        'title': 'Post a Job',
        'action': 'Post Job',
    })


@login_required
@corporate_client_required
def corporate_client_job_edit(request, job_pk):
    """Allow Corporate Client to edit their Job Posting."""
    corp = _get_corporate_client(request.user)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=corp)
    if request.method == 'POST':
        form = CorporateClientJobRequirementForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.job_title}' updated successfully.")
            return redirect('corporate_client_dashboard')
    else:
        form = CorporateClientJobRequirementForm(instance=job)
    return render(request, 'myspace/client/job_form.html', {
        'form': form,
        'corp': corp,
        'job': job,
        'title': 'Edit Job',
        'action': 'Save Changes',
    })


@login_required
@corporate_client_required
def corporate_client_job_delete(request, job_pk):
    """Allow Corporate Client to delete their Job Posting."""
    corp = _get_corporate_client(request.user)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=corp)
    if request.method == 'POST':
        title = job.job_title
        job.delete()
        messages.success(request, f"Job requirement '{title}' deleted.")
        return redirect('corporate_client_dashboard')
    return render(request, 'myspace/client/job_confirm_delete.html', {
        'corp': corp,
        'job': job,
    })



# ─── Jobs ─────────────────────────────────────────────────────────────────────

@login_required
@corporate_client_required
def corporate_client_my_jobs(request):
    """List only the jobs that belong to this Corporate Client."""
    corp = _get_corporate_client(request.user)
    jobs = JobRequirement.objects.filter(client=corp).annotate(
        submission_count=Count('submissions'),
        shortlist_count=Count('submissions', filter=Q(submissions__status='shortlisted')),
        interview_count=Count('submissions', filter=Q(submissions__status='interview_scheduled')),
        select_yet_to_offer_count=Count('submissions', filter=Q(submissions__status='selected_yet_to_offer')),
        offered_yet_to_join_count=Count('submissions', filter=Q(submissions__status='offered_yet_to_join')),
        joined_count=Count('submissions', filter=Q(submissions__status='joined'))
    ).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)

    totals = {
        'num_positions': sum(j.num_positions for j in jobs),
        'submissions': sum(j.submission_count for j in jobs),
        'shortlisted': sum(j.shortlist_count for j in jobs),
        'interviews': sum(j.interview_count for j in jobs),
        'select_yet_to_offer': sum(j.select_yet_to_offer_count for j in jobs),
        'offered_yet_to_join': sum(j.offered_yet_to_join_count for j in jobs),
        'joined': sum(j.joined_count for j in jobs),
    }

    for job in jobs:
        if job.required_skills:
            # Clean and strip newlines/carriage returns
            skills_text = job.required_skills.replace('\r', ' ').replace('\n', ' ').strip()
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            if len(skills) > 2:
                short_text = f"{skills[0]}, {skills[1]}"
                if len(short_text) > 30:
                    job.required_skills_short = short_text[:30] + " ......"
                else:
                    job.required_skills_short = short_text + " ......"
            else:
                if len(skills_text) > 30:
                    job.required_skills_short = skills_text[:30] + " ......"
                else:
                    job.required_skills_short = skills_text
        else:
            job.required_skills_short = ""

    return render(request, 'myspace/client/my_jobs.html', {
        'corp': corp,
        'jobs': jobs,
        'totals': totals,
        'status_filter': status_filter,
        'status_choices': JobRequirement.STATUS_CHOICES,
    })


@login_required
@corporate_client_required
def corporate_client_job_candidates(request, job_pk):
    """
    View candidates submitted for a specific job.
    Also shows the Corporate Client's cart selection for this job.
    """
    corp = _get_corporate_client(request.user)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=corp)
    submissions = CandidateSubmission.objects.filter(
        job=job
    ).select_related('candidate', 'submitted_by').order_by('-created_at')

    # IDs already in cart for this job
    cart_candidate_ids = set(
        CandidateCart.objects.filter(client=corp, job=job).values_list('candidate_id', flat=True)
    )

    # Fetch credential requests for these candidate IDs
    candidate_ids = [sub.candidate.id for sub in submissions]
    credential_requests = {
        req.candidate_id: req
        for req in CorporateCredentialRequest.objects.filter(client=corp, candidate_id__in=candidate_ids)
    }
    for sub in submissions:
        sub.candidate.credential_request = credential_requests.get(sub.candidate.id)

    return render(request, 'myspace/client/job_candidates.html', {
        'corp': corp,
        'job': job,
        'submissions': submissions,
        'cart_candidate_ids': cart_candidate_ids,
    })


# ─── Cart ─────────────────────────────────────────────────────────────────────

@login_required
@corporate_client_required
def corporate_client_add_to_cart(request, job_pk, candidate_pk):
    """
    Add a submitted candidate to the corporate client's cart.
    Triggers a recruiter email notification.
    """
    corp = _get_corporate_client(request.user)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=corp)
    # Ensure the candidate is actually submitted to this job
    submission = get_object_or_404(CandidateSubmission, job=job, candidate_id=candidate_pk)
    candidate = submission.candidate

    cart_item, created = CandidateCart.objects.get_or_create(
        client=corp,
        job=job,
        candidate=candidate
    )

    # Automatically create/reset credentials request
    req, req_created = CorporateCredentialRequest.objects.get_or_create(
        client=corp,
        candidate=candidate
    )
    if not req_created and req.status == 'rejected':
        req.status = 'pending'
        req.save()

    if created:
        # Mark submission as 'shortlisted'
        if submission.status == 'submitted':
            submission.status = 'shortlisted'
            submission.save()
            SubmissionStatusHistory.objects.create(
                submission=submission,
                status='shortlisted',
                changed_by=request.user,
                comments='Candidate added to client cart'
            )

        # Fire email notification to recruiter
        recruiter = candidate.recruiter
        try:
            from notifications.tasks import send_corporate_cart_notification_task
            send_corporate_cart_notification_task.delay(corp.id, candidate.id, job.id, recruiter.id)
        except Exception as e:
            print(f"Failed to dispatch cart notification task: {e}")

        messages.success(request, f"'{candidate.full_name}' added to your shortlist. Recruiter notified and credentials requested.")
    else:
        messages.info(request, f"'{candidate.full_name}' is already in your shortlist for this job.")

    return redirect('corporate_client_job_candidates', job_pk=job_pk)


@login_required
@corporate_client_required
def corporate_client_remove_from_cart(request, job_pk, candidate_pk):
    """Remove a candidate from the cart."""
    corp = _get_corporate_client(request.user)
    job = get_object_or_404(JobRequirement, pk=job_pk, client=corp)
    cart_item = get_object_or_404(CandidateCart, client=corp, job=job, candidate_id=candidate_pk)
    if request.method == 'POST':
        cart_item.delete()
        messages.success(request, 'Candidate removed from shortlist.')
    return redirect('corporate_client_job_candidates', job_pk=job_pk)


@login_required
@corporate_client_required
def corporate_client_cart(request):
    """View all shortlisted candidates across all jobs."""
    corp = _get_corporate_client(request.user)
    cart_items = CandidateCart.objects.filter(
        client=corp
    ).select_related('candidate', 'job').order_by('-created_at')

    # Fetch credential requests for these candidate IDs
    candidate_ids = [item.candidate.id for item in cart_items]
    credential_requests = {
        req.candidate_id: req
        for req in CorporateCredentialRequest.objects.filter(client=corp, candidate_id__in=candidate_ids)
    }
    for item in cart_items:
        item.candidate.credential_request = credential_requests.get(item.candidate.id)

    return render(request, 'myspace/client/cart.html', {
        'corp': corp,
        'cart_items': cart_items,
    })


# ─── Status History ───────────────────────────────────────────────────────────

@login_required
@corporate_client_required
def corporate_client_submission_history(request, submission_pk):
    """View the full status history of a submission."""
    corp = _get_corporate_client(request.user)
    submission = get_object_or_404(CandidateSubmission, pk=submission_pk, job__client=corp)
    history = submission.status_history.select_related('changed_by').order_by('-changed_at')
    return render(request, 'myspace/client/submission_history.html', {
        'corp': corp,
        'submission': submission,
        'history': history,
    })


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required
@corporate_client_required
def corporate_client_profile(request):
    """View the Corporate Client's own profile."""
    corp = _get_corporate_client(request.user)
    return render(request, 'myspace/client/profile.html', {
        'corp': corp,
    })


@login_required
def download_corporate_candidate_document(request, candidate_id, doc_type):
    from django.core.exceptions import PermissionDenied
    from django.http import FileResponse, Http404

    candidate = get_object_or_404(CorporateCandidate, id=candidate_id)
    
    # Access control: admin, recruiter owner of the candidate, or corporate client with approved request
    has_access = False
    if request.user.role == 'admin':
        has_access = True
    elif request.user.role == 'recruiter':
        if candidate.recruiter == request.user:
            has_access = True
    elif request.user.role == 'corporate_client':
        try:
            corp = CorporateClient.objects.get(user=request.user)
            has_access = CorporateCredentialRequest.objects.filter(
                client=corp,
                candidate=candidate,
                status='approved'
            ).exists()
        except CorporateClient.DoesNotExist:
            pass
            
    if not has_access:
        raise PermissionDenied("You do not have access to these credentials.")
        
    if doc_type == 'resume':
        file_field = candidate.resume
        label = "resume"
    elif doc_type == 'bgv':
        file_field = candidate.bgv_verification
        label = "BGV verification"
    elif doc_type == 'evaluation':
        file_field = candidate.evaluation_certificate
        label = "evaluation certificate"
    else:
        raise Http404("Document type not found.")
        
    if not file_field or not file_field.name:
        messages.error(request, f"No {label} uploaded for candidate {candidate.full_name}.")
        return redirect(request.META.get('HTTP_REFERER', 'corporate_client_dashboard'))
        
    if hasattr(file_field, 'url') and file_field.url.startswith(('http://', 'https://')):
        return redirect(file_field.url)
        
    try:
        response = FileResponse(file_field.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{file_field.name.split("/")[-1]}"'
        return response
    except (OSError, ValueError):
        if hasattr(file_field, 'url'):
            return redirect(file_field.url)
        raise


@login_required
def download_corporate_candidate_resume(request, candidate_id):
    return download_corporate_candidate_document(request, candidate_id, 'resume')


@login_required
@corporate_client_required
def corporate_candidate_detail(request, candidate_pk):
    """View the complete profile of a Corporate Candidate."""
    corp = _get_corporate_client(request.user)
    candidate = get_object_or_404(CorporateCandidate, pk=candidate_pk)
    
    # Ensure this candidate has a submission for one of the client's jobs
    submission = get_object_or_404(CandidateSubmission, candidate=candidate, job__client=corp)
    
    # Check if the credential request is approved
    has_credentials_access = CorporateCredentialRequest.objects.filter(
        client=corp,
        candidate=candidate,
        status='approved'
    ).exists()

    return render(request, 'myspace/client/candidate_detail.html', {
        'corp': corp,
        'candidate': candidate,
        'submission': submission,
        'has_credentials_access': has_credentials_access,
    })


@login_required
@corporate_client_required
def corporate_client_servicenow_candidates(request, module_name):
    """Filter and display submitted candidates matching a ServiceNow module."""
    corp = _get_corporate_client(request.user)
    if not corp.is_servicenow_client:
        messages.error(request, "ServiceNow Dashboard is not enabled for your account.")
        return redirect('corporate_client_dashboard')

    submissions = CandidateSubmission.objects.filter(
        job__client=corp,
        candidate__servicenow_module=module_name
    ).select_related('candidate', 'job').order_by('-created_at')

    credential_requests = {
        req.candidate_id: req
        for req in CorporateCredentialRequest.objects.filter(client=corp)
    }

    cart_candidate_ids = set(
        CandidateCart.objects.filter(client=corp).values_list('candidate_id', flat=True)
    )

    for sub in submissions:
        sub.candidate.credential_request = credential_requests.get(sub.candidate.id)

    return render(request, 'myspace/client/servicenow_candidates.html', {
        'corp': corp,
        'module_name': module_name,
        'submissions': submissions,
        'cart_candidate_ids': cart_candidate_ids,
    })

