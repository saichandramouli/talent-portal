from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.decorators import manager_required
from accounts.models import User
from myspace.models import CorporateClient, JobRequirement, CandidateSubmission

@login_required
@manager_required
def manager_dashboard(request):
    # Recruiters managed by the current manager
    recruiters = User.objects.filter(manager=request.user, role='recruiter')
    cwr_recruiters = recruiters.filter(recruiter_type='cwr')
    fte_recruiters = recruiters.filter(recruiter_type='fte')
    
    # Clients handled by these recruiters
    clients = CorporateClient.objects.filter(
        recruiter_assignments__recruiter__in=recruiters
    ).distinct().order_by('company_name')
    
    # Job requirements created by these recruiters
    jobs = JobRequirement.objects.filter(
        creator__in=recruiters
    ).select_related('client', 'creator').order_by('-created_at')
    
    # Candidate submissions made by these recruiters
    submissions = CandidateSubmission.objects.filter(
        submitted_by__in=recruiters
    ).select_related('job', 'candidate', 'submitted_by').order_by('-created_at')
    
    # Statistics and Metrics
    total_recruiters = recruiters.count()
    total_cwr = cwr_recruiters.count()
    total_fte = fte_recruiters.count()
    total_clients = clients.count()
    total_jobs = jobs.count()
    total_submissions = submissions.count()
    
    # Submissions status breakdown
    status_counts = submissions.values('status').annotate(count=Count('id'))
    status_summary = {item['status']: item['count'] for item in status_counts}

    context = {
        'recruiters': recruiters,
        'cwr_recruiters': cwr_recruiters,
        'fte_recruiters': fte_recruiters,
        'clients': clients,
        'jobs': jobs,
        'submissions': submissions,
        'total_recruiters': total_recruiters,
        'total_cwr': total_cwr,
        'total_fte': total_fte,
        'total_clients': total_clients,
        'total_jobs': total_jobs,
        'total_submissions': total_submissions,
        'status_summary': status_summary,
    }
    return render(request, 'myspace/manager/dashboard.html', context)
