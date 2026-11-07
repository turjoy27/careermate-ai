from django.contrib import admin
from .models import JobListing, SavedJob


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company_name',
        'location',
        'job_type',
        'workplace_type',
        'experience_level',
        'is_active',
        'created_at',
    )
    list_filter = ('job_type', 'workplace_type', 'experience_level', 'is_active', 'created_at')
    search_fields = ('title', 'company_name', 'location', 'required_skills_raw', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Overview', {
            'fields': ('title', 'company_name', 'company_logo_url', 'location', 'is_active')
        }),
        ('Classification & Compensation', {
            'fields': ('job_type', 'workplace_type', 'experience_level', 'salary_range')
        }),
        ('Job Description & Requirements', {
            'fields': ('description', 'responsibilities', 'requirements', 'required_skills_raw', 'preferred_skills_raw')
        }),
        ('Application Details', {
            'fields': ('apply_url', 'apply_email')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('profile', 'job', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('profile__user__email', 'job__title', 'job__company_name')
