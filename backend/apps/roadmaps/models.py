from django.db import models
from django.utils import timezone
from apps.accounts.models import User, UserProfile


class LearningRoadmap(models.Model):
    """Personalized progressive learning roadmap for a candidate's target career."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='roadmaps'
    )
    title = models.CharField(max_length=200)
    target_role = models.CharField(max_length=200)
    skill_gap_summary = models.TextField(blank=True)
    estimated_duration = models.CharField(max_length=100, default='16 Weeks (10 hrs/week)')
    total_milestones = models.IntegerField(default=0)
    completed_milestones = models.IntegerField(default=0)
    progress_percentage = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Learning Roadmap'
        verbose_name_plural = 'Learning Roadmaps'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.profile.user.email}"

    def recalculate_progress(self):
        """Recalculates milestone completion metrics and saves the updated percentages."""
        all_milestones = RoadmapMilestone.objects.filter(stage__roadmap=self)
        total = all_milestones.count()
        completed = all_milestones.filter(is_completed=True).count()

        self.total_milestones = total
        self.completed_milestones = completed
        self.progress_percentage = int(round((completed / total) * 100)) if total > 0 else 0
        self.save(update_fields=['total_milestones', 'completed_milestones', 'progress_percentage', 'updated_at'])
        return self.progress_percentage


class RoadmapStage(models.Model):
    """A learning phase: Beginner, Intermediate, or Advanced."""

    STAGE_CHOICES = (
        ('beginner', 'Beginner / Foundations'),
        ('intermediate', 'Intermediate / Core Mastery'),
        ('advanced', 'Advanced / Production Ready'),
    )

    roadmap = models.ForeignKey(
        LearningRoadmap,
        on_delete=models.CASCADE,
        related_name='stages'
    )
    stage_level = models.CharField(max_length=50, choices=STAGE_CHOICES)
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=1)
    duration_weeks = models.CharField(max_length=100, default='4-6 Weeks')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Roadmap Stage'
        verbose_name_plural = 'Roadmap Stages'
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_stage_level_display()})"

    @property
    def completed_count(self):
        return self.milestones.filter(is_completed=True).count()

    @property
    def total_count(self):
        return self.milestones.count()


class RoadmapMilestone(models.Model):
    """Actionable milestone checklist within a stage."""

    stage = models.ForeignKey(
        RoadmapStage,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=255)
    skills_covered = models.CharField(max_length=255, blank=True)
    practical_task = models.TextField(blank=True)
    order = models.IntegerField(default=1)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Roadmap Milestone'
        verbose_name_plural = 'Roadmap Milestones'
        ordering = ['order']

    def __str__(self):
        return f"Milestone: {self.title} [{ 'Done' if self.is_completed else 'Pending' }]"


class RoadmapResource(models.Model):
    """Recommended learning resource associated with a stage."""

    RESOURCE_CHOICES = (
        ('documentation', 'Official Documentation'),
        ('course', 'Online Course'),
        ('video', 'Video Tutorial'),
        ('project', 'Practical Project Task'),
        ('article', 'Guide / Article'),
    )

    stage = models.ForeignKey(
        RoadmapStage,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_CHOICES, default='documentation')
    url = models.URLField(blank=True)
    is_free = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Roadmap Resource'
        verbose_name_plural = 'Roadmap Resources'

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class LearningResource(models.Model):
    """Curated platform learning library manageable by admins."""

    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, help_text="e.g. Python, Frontend, SQL, DevOps, Interview Prep")
    resource_type = models.CharField(max_length=50, default='course')
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default='beginner')
    url = models.URLField()
    description = models.TextField(blank=True)
    is_free = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curated Learning Resource'
        verbose_name_plural = 'Curated Learning Resources'
        ordering = ['-is_featured', 'category', 'title']

    def __str__(self):
        return f"{self.title} [{self.category}]"


class ReportedContent(models.Model):
    """User feedback, content reporting, and moderation tickets."""

    CATEGORY_CHOICES = (
        ('job_issue', 'Job Listing Issue / Broken Link'),
        ('ai_inaccuracy', 'AI Output Inaccuracy / Quality Issue'),
        ('roadmap_issue', 'Roadmap / Resource Inaccuracy'),
        ('general_feedback', 'General Feedback / Support Request'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_items'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general_feedback')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reported Content / Moderation'
        verbose_name_plural = 'Reported Content / Moderation'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} by {self.user.email if self.user else 'Anonymous'}"
