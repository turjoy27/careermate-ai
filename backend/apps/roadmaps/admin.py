from django.contrib import admin
from django.utils import timezone
from .models import (
    LearningResource,
    LearningRoadmap,
    ReportedContent,
    RoadmapMilestone,
    RoadmapResource,
    RoadmapStage,
)

# Customize Admin Site Branding
admin.site.site_header = "CareerMate AI Administration"
admin.site.site_title = "CareerMate AI Portal"
admin.site.index_title = "Platform Operations, Analytics & Moderation"


class RoadmapResourceInline(admin.TabularInline):
    model = RoadmapResource
    extra = 0


class RoadmapMilestoneInline(admin.TabularInline):
    model = RoadmapMilestone
    extra = 0


class RoadmapStageInline(admin.StackedInline):
    model = RoadmapStage
    extra = 0


@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'profile',
        'target_role',
        'total_milestones',
        'completed_milestones',
        'progress_percentage',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'target_role', 'profile__user__email')
    readonly_fields = ('total_milestones', 'completed_milestones', 'progress_percentage', 'created_at', 'updated_at')
    inlines = [RoadmapStageInline]


@admin.register(RoadmapStage)
class RoadmapStageAdmin(admin.ModelAdmin):
    list_display = ('title', 'roadmap', 'stage_level', 'order', 'duration_weeks')
    list_filter = ('stage_level',)
    search_fields = ('title', 'roadmap__title')
    inlines = [RoadmapMilestoneInline, RoadmapResourceInline]


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resource_type', 'difficulty', 'is_free', 'is_featured', 'created_at')
    list_filter = ('category', 'resource_type', 'difficulty', 'is_free', 'is_featured')
    search_fields = ('title', 'category', 'description')
    list_editable = ('is_featured', 'is_free')


@admin.register(ReportedContent)
class ReportedContentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'category', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('subject', 'description', 'user__email', 'admin_notes')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_resolved', 'mark_investigating', 'mark_dismissed']

    @admin.action(description="Mark selected tickets as Resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved', updated_at=timezone.now())

    @admin.action(description="Mark selected tickets as Under Investigation")
    def mark_investigating(self, request, queryset):
        queryset.update(status='investigating', updated_at=timezone.now())

    @admin.action(description="Mark selected tickets as Dismissed")
    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed', updated_at=timezone.now())
