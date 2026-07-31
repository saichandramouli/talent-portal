from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from accounts.decorators import ceo_required
from accounts.models import User
from myspace.models import CorporateClient, JobRequirement, CandidateSubmission
from candidates.models import Candidate, JobTitle, Skill
from teams.models import TechnologyStack, Team

@login_required
@ceo_required
def ceo_dashboard(request):
    # Overall Company Statistics
    total_managers = User.objects.filter(role='manager').count()
    recruiters = User.objects.filter(role='recruiter')
    total_recruiters = recruiters.count()
    total_cwr = recruiters.filter(recruiter_type='cwr').count()
    total_fte = recruiters.filter(recruiter_type='fte').count()
    total_clients = CorporateClient.objects.count()
    total_jobs = JobRequirement.objects.count()
    total_submissions = CandidateSubmission.objects.count()
    
    # Submissions status breakdown
    status_counts = CandidateSubmission.objects.values('status').annotate(count=Count('id'))
    status_summary = {item['status']: item['count'] for item in status_counts}

    # Grouping data under each manager
    managers_data = []
    managers = User.objects.filter(role='manager').order_by('full_name')
    for mgr in managers:
        mgr_recruiters = User.objects.filter(manager=mgr, role='recruiter')
        mgr_cwr = mgr_recruiters.filter(recruiter_type='cwr')
        mgr_fte = mgr_recruiters.filter(recruiter_type='fte')
        
        # Clients under this manager's recruiters
        mgr_clients = CorporateClient.objects.filter(
            recruiter_assignments__recruiter__in=mgr_recruiters
        ).distinct()
        
        # Jobs under this manager's recruiters
        mgr_jobs = JobRequirement.objects.filter(
            creator__in=mgr_recruiters
        )
        
        # Submissions under this manager's recruiters
        mgr_subs = CandidateSubmission.objects.filter(
            submitted_by__in=mgr_recruiters
        )
        
        managers_data.append({
            'manager': mgr,
            'recruiters': mgr_recruiters,
            'cwr_recruiters': mgr_cwr,
            'fte_recruiters': mgr_fte,
            'clients_count': mgr_clients.count(),
            'jobs_count': mgr_jobs.count(),
            'submissions_count': mgr_subs.count(),
        })

    # Recruiters without any manager assigned
    # New Datasets for Detailed Tables
    corporate_clients_list = CorporateClient.objects.all().order_by('company_name')
    teams_and_stacks = Team.objects.prefetch_related('technology_stacks').all().order_by('name')

    context = {
        'total_managers': total_managers,
        'total_recruiters': total_recruiters,
        'total_cwr': total_cwr,
        'total_fte': total_fte,
        'total_clients': total_clients,
        'total_jobs': total_jobs,
        'total_submissions': total_submissions,
        'status_summary': status_summary,
        'managers_data': managers_data,
        'corporate_clients_list': corporate_clients_list,
        'teams_and_stacks': teams_and_stacks,
    }
    return render(request, 'myspace/ceo/dashboard.html', context)

@login_required
@ceo_required
def ceo_hiring_directory(request):
    # Candidate Profiles & Technology Wise Hiring
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

    context = {
        # Candidate Profiles/Tech hiring data
        'candidates': candidates,
        'all_stacks': all_stacks,
        'all_job_titles': all_job_titles,
        'all_skills': all_skills,
        'selected_stack': selected_stack,
        'job_title_filter': job_title_filter,
        'skills_filter': skills_filter,
        'search_query': search_query,
    }
    return render(request, 'myspace/ceo/hiring_directory.html', context)
