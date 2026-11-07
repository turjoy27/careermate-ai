from django.contrib import admin
from .models import Resume, ResumeEducation, ResumeExperience, ResumeProject


class ResumeEducationInline(admin.TabularInline):
    model = ResumeEducation
    extra = 0


class ResumeExperienceInline(admin.TabularInline):
    model = ResumeExperience
    extra = 0


class ResumeProjectInline(admin.TabularInline):
    model = ResumeProject
    extra = 0


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'full_name', 'email', 'profile', 'template_style', 'updated_at')
    search_fields = ('title', 'full_name', 'email', 'profile__user__email')
    list_filter = ('template_style', 'updated_at')
    inlines = [ResumeEducationInline, ResumeExperienceInline, ResumeProjectInline]
