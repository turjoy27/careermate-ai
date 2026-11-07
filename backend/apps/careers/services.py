"""
Service layer coordinating profile compilation, AI generation, and persistence.
"""

from django.db import transaction
from apps.accounts.models import UserProfile
from apps.ai_services.client import GeminiService
from .models import (
    CareerRecommendation,
    CareerRecommendationSession,
    SkillGapReport,
)


class CareerRecommendationService:
    """Orchestrates candidate profile ingestion, AI recommendation, and history tracking."""

    @staticmethod
    def gather_profile_context(profile: UserProfile) -> dict:
        """Serializes user profile, skills, education, and experiences into AI prompt context."""
        user = profile.user
        educations = [
            {
                'institution': edu.institution,
                'degree': edu.degree,
                'field_of_study': edu.field_of_study,
                'is_current': edu.is_current,
                'grade': edu.grade or ''
            }
            for edu in profile.educations.all()
        ]

        skills = [
            {
                'skill_name': s.skill_name,
                'category': s.category,
                'proficiency': s.proficiency
            }
            for s in profile.skills.all()
        ]

        experiences = [
            {
                'company': exp.company,
                'position': exp.position,
                'description': exp.description
            }
            for exp in profile.experiences.all()
        ]

        return {
            'role': user.get_role_display(),
            'headline': profile.headline,
            'target_career': profile.target_career,
            'summary': profile.summary,
            'city': profile.city,
            'country': profile.country,
            'educations': educations,
            'skills': skills,
            'experiences': experiences,
        }

    @classmethod
    def generate_recommendations(
        cls,
        profile: UserProfile,
        preferences: dict = None,
        ai_service: GeminiService = None
    ) -> CareerRecommendationSession:
        """
        Executes end-to-end career recommendation process and persists results atomically.
        """
        profile_data = cls.gather_profile_context(profile)

        # Ensure minimal data presence for realistic recommendations
        if not profile_data['skills'] and not profile_data['educations']:
            raise ValueError(
                "Please add at least one education record or skill in your profile before requesting AI career recommendations."
            )

        service = ai_service or GeminiService()
        ai_response = service.generate_career_recommendations(profile_data, preferences)

        with transaction.atomic():
            session = CareerRecommendationSession.objects.create(
                profile=profile,
                interests=preferences.get('interests', '') if preferences else '',
                work_preference=preferences.get('work_preference', '') if preferences else '',
                target_industries=preferences.get('target_industries', '') if preferences else '',
                target_analysis=ai_response.target_analysis,
                readiness_level=ai_response.readiness_level,
            )

            for item in ai_response.recommendations:
                rec = CareerRecommendation.objects.create(
                    session=session,
                    profile=profile,
                    title=item.title,
                    match_score=item.match_score,
                    suitability_reason=item.suitability_reason,
                    market_outlook_bd=item.market_outlook_bd,
                    required_skills=item.required_skills,
                    matched_skills=item.matched_skills,
                    missing_skills=item.missing_skills,
                    growth_potential=item.growth_potential,
                    recommended_next_steps=item.recommended_next_steps,
                )

                SkillGapReport.objects.create(
                    recommendation=rec,
                    profile=profile,
                    target_role=item.title,
                    match_percentage=item.match_score,
                    strengths=item.matched_skills,
                    critical_missing_skills=item.missing_skills[:3],
                    learning_priority=item.missing_skills,
                )

        return session
