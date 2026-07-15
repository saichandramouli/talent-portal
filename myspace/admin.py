from django.contrib import admin
from .models import (
    CorporateClient, RecruiterClientAssignment, CorporateCandidate,
    JobRequirement, CandidateSubmission, SubmissionStatusHistory, CandidateCart,
    CorporateCredentialRequest
)


@admin.register(CorporateClient)
class CorporateClientAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('company_name', 'contact_phone')


@admin.register(RecruiterClientAssignment)
class RecruiterClientAssignmentAdmin(admin.ModelAdmin):
    list_display = ('recruiter', 'client', 'assigned_at')
    list_filter = ('client',)
    search_fields = ('recruiter__email', 'client__company_name')


@admin.register(CorporateCandidate)
class CorporateCandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'technology_stack', 'total_experience', 'rate_card', 'recruiter', 'status')
    list_filter = ('status', 'recruiter')
    search_fields = ('full_name', 'email', 'technology_stack')


@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'client', 'employment_type', 'experience', 'status', 'created_at')
    list_filter = ('status', 'employment_type', 'client')
    search_fields = ('job_title', 'client__company_name')


@admin.register(CandidateSubmission)
class CandidateSubmissionAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'submitted_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('candidate__full_name', 'job__job_title')


@admin.register(SubmissionStatusHistory)
class SubmissionStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('submission', 'status', 'changed_by', 'changed_at')
    list_filter = ('status',)
    search_fields = ('submission__candidate__full_name',)


@admin.register(CandidateCart)
class CandidateCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'candidate', 'job', 'created_at')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__full_name', 'candidate__full_name')


@admin.register(CorporateCredentialRequest)
class CorporateCredentialRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'candidate', 'status', 'created_at')
    list_filter = ('status', 'client')
    search_fields = ('client__company_name', 'candidate__full_name')

