from django.db import models
from apps.accounts.models import UserProfile


class Resume(models.Model):
    """Primary Resume model storing contact info, summary, and style settings."""

    TEMPLATE_CHOICES = (
        ('modern_clean', 'Modern Clean (ATS Optimized)'),
        ('classic_professional', 'Classic Professional'),
    )

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    title = models.CharField(max_length=200, default='My Resume')
    target_role = models.CharField(max_length=200, blank=True)

    # Personal Information
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=150, blank=True, default='Dhaka, Bangladesh')
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Content
    professional_summary = models.TextField(blank=True)
    skills_raw = models.TextField(
        blank=True,
        help_text="Comma-separated or bullet list of technical & professional skills"
    )

    template_style = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default='modern_clean'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.full_name})"

    @property
    def skills_list(self):
        if not self.skills_raw:
            return []
        # Split by comma or newline
        lines = [item.strip('•- \t\r') for line in self.skills_raw.splitlines() for item in line.split(',')]
        return [item for item in lines if item]


class ResumeEducation(models.Model):
    """Education records within a specific resume."""

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='educations'
    )
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    start_date = models.CharField(max_length=50)
    end_date = models.CharField(max_length=50, blank=True, default='Present')
    grade = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class ResumeExperience(models.Model):
    """Work and internship experience items for a resume."""

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.CharField(max_length=50)
    end_date = models.CharField(max_length=50, blank=True, default='Present')
    description = models.TextField(blank=True, help_text="Bullet points describing responsibilities and achievements")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.position} at {self.company}"


class ResumeProject(models.Model):
    """Projects itemized within a resume."""

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=255)
    tech_stack = models.CharField(max_length=255, blank=True)
    live_link = models.URLField(blank=True)
    github_link = models.URLField(blank=True)
    description = models.TextField(blank=True, help_text="Impact and features built")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title
