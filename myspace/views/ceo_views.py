from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.decorators import ceo_required
from accounts.models import User
from myspace.models import CorporateClient, JobRequirement, CandidateSubmission

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
    unassigned_recruiters = User.objects.filter(role='recruiter', manager__isnull=True)

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
        'unassigned_recruiters': unassigned_recruiters,
    }
    return render(request, 'myspace/ceo/dashboard.html', context)
