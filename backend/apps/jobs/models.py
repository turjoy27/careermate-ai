from django.db import models
from apps.accounts.models import UserProfile


class JobListing(models.Model):
    """Job listing storing job description, required skills, and employment metadata."""

    JOB_TYPE_CHOICES = (
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    )

    WORKPLACE_CHOICES = (
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
    )

    EXP_LEVEL_CHOICES = (
        ('entry', 'Entry-level / Fresh Graduate'),
        ('mid', 'Mid-level (1-3 yrs)'),
        ('senior', 'Senior (3+ yrs)'),
    )

    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    company_logo_url = models.URLField(blank=True)
    location = models.CharField(max_length=150, default='Dhaka, Bangladesh')
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES, default='full_time')
    workplace_type = models.CharField(max_length=50, choices=WORKPLACE_CHOICES, default='onsite')
    experience_level = models.CharField(max_length=50, choices=EXP_LEVEL_CHOICES, default='entry')
    salary_range = models.CharField(max_length=100, blank=True, help_text="e.g. BDT 35,000 - 50,000 / month")

    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)

    required_skills_raw = models.TextField(
        help_text="Comma-separated required skills (e.g., Python, Django, MySQL, REST APIs)"
    )
    preferred_skills_raw = models.TextField(
        blank=True,
        help_text="Comma-separated nice-to-have skills (e.g., Docker, AWS, Redis)"
    )

    apply_url = models.URLField(blank=True)
    apply_email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Listing'
        verbose_name_plural = 'Job Listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company_name} ({self.location})"

    def _parse_skills(self, raw_text: str) -> list[str]:
        if not raw_text:
            return []
        items = [s.strip() for s in raw_text.split(',') if s.strip()]
        return items

    @property
    def required_skills_list(self) -> list[str]:
        return self._parse_skills(self.required_skills_raw)

    @property
    def preferred_skills_list(self) -> list[str]:
        return self._parse_skills(self.preferred_skills_raw)


class SavedJob(models.Model):
    """User bookmarked job listing."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='saved_jobs'
    )
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name='saved_by_users'
    )
    notes = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        unique_together = ('profile', 'job')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.profile.user.email} saved {self.job.title}"
