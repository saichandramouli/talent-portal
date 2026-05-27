from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.decorators import client_required
from .models import Cart
from candidates.models import Candidate
from teams.models import TechnologyStack
from notifications.utils import send_cart_notification

@login_required
@client_required
def client_dashboard(request):
    client = request.user
    candidates = Candidate.objects.all().order_by('-created_at')
    
    # Get all tech stacks for filter dropdown
    all_stacks = TechnologyStack.objects.all()
    
    # Get values for filter dropdowns/searches
    selected_stack = request.GET.get('stack', '')
    min_exp = request.GET.get('min_exp', '')
    max_exp = request.GET.get('max_exp', '')
    max_rate = request.GET.get('max_rate', '')
    location_filter = request.GET.get('location', '')
    availability_filter = request.GET.get('availability', '')
    search_query = request.GET.get('q', '')

    # Apply Search
    if search_query:
        candidates = candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(technical_stack__name__icontains=search_query) |
            Q(location__icontains=search_query)
        ).distinct()

    # Apply Filters
    if selected_stack:
        candidates = candidates.filter(technical_stack__id=selected_stack)
        
    if min_exp:
        candidates = candidates.filter(years_of_experience__gte=min_exp)
        
    if max_exp:
        candidates = candidates.filter(years_of_experience__lte=max_exp)
        
    if max_rate:
        candidates = candidates.filter(rate_card__lte=max_rate)
        
    if location_filter:
        candidates = candidates.filter(location__icontains=location_filter)
        
    if availability_filter:
        candidates = candidates.filter(availability__icontains=availability_filter)

    # Get client's current cart candidate IDs to show state
    cart_candidate_ids = set(Cart.objects.filter(client=client).values_list('candidate_id', flat=True))

    context = {
        'candidates': candidates,
        'all_stacks': all_stacks,
        'cart_candidate_ids': cart_candidate_ids,
        # Maintain form state
        'selected_stack': selected_stack,
        'min_exp': min_exp,
        'max_exp': max_exp,
        'max_rate': max_rate,
        'location_filter': location_filter,
        'availability_filter': availability_filter,
        'search_query': search_query,
    }
    return render(request, 'clients/client_dashboard.html', context)

@login_required
@client_required
def cart_view(request):
    client = request.user
    cart_items = Cart.objects.filter(client=client).select_related('candidate', 'candidate__recruiter')
    return render(request, 'clients/cart_view.html', {'cart_items': cart_items})

@login_required
@client_required
def add_to_cart(request, candidate_id):
    client = request.user
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Prevent duplicates
    cart_item, created = Cart.objects.get_or_create(client=client, candidate=candidate)
    
    if created:
        # Trigger email notification to the recruiter
        send_cart_notification(client, candidate)
        messages.success(request, f"Candidate {candidate.full_name} has been added to your cart. A notification email was sent to their recruiter, {candidate.recruiter.full_name}.")
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
