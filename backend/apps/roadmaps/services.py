"""
Service layer orchestrating personalized learning roadmaps and milestone progress tracking.
"""

from django.db import transaction
from django.utils import timezone
from apps.accounts.models import UserProfile
from apps.ai_services.client import GeminiService
from .models import LearningRoadmap, RoadmapMilestone, RoadmapResource, RoadmapStage


class RoadmapService:
    """Business logic for AI roadmap generation and milestone progress tracking."""

    @classmethod
    def generate_roadmap(
        cls,
        profile: UserProfile,
        target_role: str,
        experience_level: str = "beginner",
        weekly_hours: int = 10,
        ai_service: GeminiService = None
    ) -> LearningRoadmap:
        """
        Synthesizes candidate profile, queries Gemini for a structured 3-stage curriculum,
        and records stages, milestones, and resources in MySQL.
        """
        clean_role = target_role.strip() or profile.target_career or "Software Engineer"
        user_skills = [s.skill_name for s in profile.skills.all()]

        service = ai_service or GeminiService()
        ai_response = service.generate_learning_roadmap(
            target_role=clean_role,
            user_skills=user_skills,
            experience_level=experience_level,
            weekly_hours=weekly_hours
        )

        with transaction.atomic():
            roadmap = LearningRoadmap.objects.create(
                profile=profile,
                title=f"{clean_role} Career Roadmap",
                target_role=clean_role,
                skill_gap_summary=ai_response.skill_gap_summary,
                estimated_duration=ai_response.estimated_total_duration,
                is_active=True
            )

            total_milestones_count = 0

            for stage_order, stage_item in enumerate(ai_response.stages, start=1):
                stage_obj = RoadmapStage.objects.create(
                    roadmap=roadmap,
                    stage_level=stage_item.stage_level.lower(),
                    title=stage_item.title,
                    order=stage_order,
                    duration_weeks=stage_item.duration_weeks,
                    description=stage_item.description
                )

                # Add milestones
                for m_order, m_item in enumerate(stage_item.milestones, start=1):
                    skills_joined = ", ".join(m_item.skills_covered) if isinstance(m_item.skills_covered, list) else str(m_item.skills_covered)
                    RoadmapMilestone.objects.create(
                        stage=stage_obj,
                        title=m_item.title,
                        skills_covered=skills_joined,
                        practical_task=m_item.practical_task,
                        order=m_order,
                        is_completed=False
                    )
                    total_milestones_count += 1

                # Add recommended resources
                for r_item in stage_item.recommended_resources:
                    RoadmapResource.objects.create(
                        stage=stage_obj,
                        title=r_item.title,
                        resource_type=r_item.resource_type.lower() if r_item.resource_type else 'documentation',
                        url=r_item.url or "",
                        is_free=r_item.is_free
                    )

            roadmap.total_milestones = total_milestones_count
            roadmap.completed_milestones = 0
            roadmap.progress_percentage = 0
            roadmap.save(update_fields=['total_milestones', 'completed_milestones', 'progress_percentage'])

        return roadmap

    @classmethod
    def toggle_milestone(cls, milestone: RoadmapMilestone, is_completed: bool = None) -> dict:
        """
        Toggles milestone completion status, updates timestamp, and recalculates roadmap progress.
        """
        with transaction.atomic():
            if is_completed is None:
                new_state = not milestone.is_completed
            else:
                new_state = bool(is_completed)

            milestone.is_completed = new_state
            milestone.completed_at = timezone.now() if new_state else None
            milestone.save(update_fields=['is_completed', 'completed_at'])

            roadmap = milestone.stage.roadmap
            new_pct = roadmap.recalculate_progress()

            stage = milestone.stage
            return {
                'milestone_id': milestone.id,
                'is_completed': milestone.is_completed,
                'stage_completed': stage.completed_count,
                'stage_total': stage.total_count,
                'roadmap_completed': roadmap.completed_milestones,
                'roadmap_total': roadmap.total_milestones,
                'roadmap_progress_percentage': new_pct,
            }
