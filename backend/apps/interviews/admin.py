from django.contrib import admin
from .models import InterviewQuestion, InterviewSession


class InterviewQuestionInline(admin.StackedInline):
    model = InterviewQuestion
    extra = 0
    readonly_fields = ('order', 'category', 'question_text', 'score', 'evaluated_at')


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('target_role', 'profile', 'difficulty', 'question_type', 'overall_score', 'is_completed', 'created_at')
    list_filter = ('difficulty', 'question_type', 'is_completed', 'created_at')
    search_fields = ('target_role', 'profile__user__email')
    inlines = [InterviewQuestionInline]


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('session', 'order', 'category', 'score', 'evaluated_at')
    list_filter = ('category', 'evaluated_at')
    search_fields = ('question_text', 'user_answer', 'session__profile__user__email')
