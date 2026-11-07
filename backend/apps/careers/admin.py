from django.contrib import admin
from .models import CareerRecommendationSession, CareerRecommendation, SkillGapReport


class CareerRecommendationInline(admin.TabularInline):
    model = CareerRecommendation
    extra = 0
    readonly_fields = ('title', 'match_score', 'created_at')


@admin.register(CareerRecommendationSession)
class CareerRecommendationSessionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'readiness_level', 'created_at')
    search_fields = ('profile__user__email', 'interests')
    inlines = [CareerRecommendationInline]


@admin.register(CareerRecommendation)
class CareerRecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'match_score', 'growth_potential', 'created_at')
    list_filter = ('growth_potential', 'created_at')
    search_fields = ('title', 'profile__user__email', 'suitability_reason')


@admin.register(SkillGapReport)
class SkillGapReportAdmin(admin.ModelAdmin):
    list_display = ('target_role', 'profile', 'match_percentage', 'created_at')
    search_fields = ('target_role', 'profile__user__email')
