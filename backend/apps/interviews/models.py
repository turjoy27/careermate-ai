from django.db import models
from apps.accounts.models import UserProfile


class InterviewSession(models.Model):
    """A simulated interview practice session."""

    DIFFICULTY_CHOICES = (
        ('junior', 'Junior / Fresh Graduate'),
        ('mid', 'Mid-Level (1-3 yrs)'),
        ('senior', 'Senior (3+ yrs)'),
    )

    QUESTION_TYPE_CHOICES = (
        ('mixed', 'Technical & HR Mixed'),
        ('technical', 'Pure Technical'),
        ('hr', 'Behavioral / HR'),
    )

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    target_role = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default='junior')
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='mixed')
    total_questions = models.IntegerField(default=3)
    overall_score = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Interview Session'
        verbose_name_plural = 'Interview Sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.target_role} ({self.get_difficulty_display()}) for {self.profile.user.email}"

    @property
    def answered_count(self):
        return self.questions.filter(score__isnull=False).count()


class InterviewQuestion(models.Model):
    """An individual question generated and evaluated in a session."""

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    order = models.IntegerField(default=1)
    category = models.CharField(max_length=50)
    question_text = models.TextField()
    intent_explanation = models.TextField(blank=True)
    sample_approach = models.TextField(blank=True)

    user_answer = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True, help_text="Score 1-10")
    feedback_summary = models.TextField(blank=True)
    strengths = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    ideal_points = models.JSONField(default=list)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
