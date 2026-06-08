from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.decorators import client_required
from .models import Cart
from candidates.models import Candidate, JobTitle, Skill
from teams.models import TechnologyStack
from notifications.tasks import send_cart_notification_task

@login_required
@client_required
def client_dashboard(request):
    client = request.user
    candidates = Candidate.objects.filter(is_on_hold=False).select_related('job_title', 'recruiter').prefetch_related('technical_stack', 'skills').order_by('-created_at')
    
    # Get all tech stacks, job titles, and skills for filter dropdowns
    all_stacks = TechnologyStack.objects.all()
    all_job_titles = JobTitle.objects.all()
    all_skills = Skill.objects.all()
    
    # Get values for filter dropdowns/searches
    selected_stack = request.GET.get('stack', '')
    job_title_filter = request.GET.get('job_title', '')
    skills_filter = request.GET.get('skills', '')
    search_query = request.GET.get('q', '')

    # Apply Search
    if search_query:
        candidates = candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(technical_stack__name__icontains=search_query) |
            Q(job_title__name__icontains=search_query) |
            Q(skills__name__icontains=search_query)
        ).distinct()

    # Apply Filters
    if selected_stack:
        candidates = candidates.filter(technical_stack__id=selected_stack)
        


    if job_title_filter:
        candidates = candidates.filter(job_title__id=job_title_filter)

    if skills_filter:
        candidates = candidates.filter(skills__id=skills_filter)

    # Get client's current cart candidate IDs to show state
    cart_candidate_ids = set(Cart.objects.filter(client=client).values_list('candidate_id', flat=True))

    context = {
        'candidates': candidates,
        'all_stacks': all_stacks,
        'all_job_titles': all_job_titles,
        'all_skills': all_skills,
        'cart_candidate_ids': cart_candidate_ids,
        # Maintain form state
        'selected_stack': selected_stack,

        'job_title_filter': job_title_filter,
        'skills_filter': skills_filter,
        'search_query': search_query,
    }
    return render(request, 'clients/client_dashboard.html', context)

@login_required
@client_required
def cart_view(request):
    client = request.user
    cart_items = Cart.objects.filter(client=client, candidate__is_on_hold=False).select_related('candidate', 'candidate__recruiter')
    
    # Map credential request status
    candidate_ids = [item.candidate.id for item in cart_items]
    from candidates.models import CredentialRequest
    for item in cart_items:
        CredentialRequest.objects.get_or_create(client=client, candidate=item.candidate)

    credential_requests = {
        req.candidate_id: req
        for req in CredentialRequest.objects.filter(client=client, candidate_id__in=candidate_ids)
    }
    
    for item in cart_items:
        item.credential_request = credential_requests.get(item.candidate.id)
        
    return render(request, 'clients/cart_view.html', {'cart_items': cart_items})

@login_required
@client_required
def add_to_cart(request, candidate_id):
    client = request.user
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if candidate.is_on_hold:
        messages.error(request, "This candidate is currently on hold and cannot be added to your cart.")
        return redirect('client_dashboard')
    
    # Prevent duplicates
    cart_item, created = Cart.objects.get_or_create(client=client, candidate=candidate)
    
    # Automatically send credential request to the recruiter
    from candidates.models import CredentialRequest
    req, req_created = CredentialRequest.objects.get_or_create(client=client, candidate=candidate)
    if not req_created and req.status == 'rejected':
        req.status = 'pending'
        req.save()

    if created:
        # Trigger email notification to the recruiter asynchronously
        try:
            send_cart_notification_task.delay(client.id, candidate.id)
            messages.success(request, f"Candidate {candidate.full_name} has been added to your cart. A credential request has been sent to their recruiter, {candidate.recruiter.full_name}.")
        except Exception as e:
            print(f"Celery task dispatch failed: {e}")
            # Fallback to direct call in debug mode, or just gracefully succeed without crashing
            messages.success(request, f"Candidate {candidate.full_name} has been added to your cart. (A credential request has been sent to their recruiter).")
    else:
        messages.warning(request, f"Candidate {candidate.full_name} is already in your cart.")
        
    return redirect('client_dashboard')

@login_required
@client_required
def remove_from_cart(request, candidate_id):
    client = request.user
    cart_item = Cart.objects.filter(client=client, candidate_id=candidate_id).first()
    
    if cart_item:
        candidate_name = cart_item.candidate.full_name
        cart_item.delete()
        messages.success(request, f"Candidate {candidate_name} removed from your cart.")
    else:
        messages.error(request, "Candidate not found in your cart.")
        
    return redirect('cart_view')
