from rest_framework import serializers
from .models import (
    LearningResource,
    LearningRoadmap,
    ReportedContent,
    RoadmapMilestone,
    RoadmapResource,
    RoadmapStage,
)


class RoadmapResourceSerializer(serializers.ModelSerializer):
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)

    class Meta:
        model = RoadmapResource
        fields = ['id', 'title', 'resource_type', 'resource_type_display', 'url', 'is_free']


class RoadmapMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadmapMilestone
        fields = ['id', 'title', 'skills_covered', 'practical_task', 'order', 'is_completed', 'completed_at']


class RoadmapStageSerializer(serializers.ModelSerializer):
    stage_level_display = serializers.CharField(source='get_stage_level_display', read_only=True)
    milestones = RoadmapMilestoneSerializer(many=True, read_only=True)
    resources = RoadmapResourceSerializer(many=True, read_only=True)
    completed_count = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoadmapStage
        fields = [
            'id', 'stage_level', 'stage_level_display', 'title', 'order',
            'duration_weeks', 'description', 'completed_count', 'total_count',
            'milestones', 'resources'
        ]


class LearningRoadmapSerializer(serializers.ModelSerializer):
    stages = RoadmapStageSerializer(many=True, read_only=True)

    class Meta:
        model = LearningRoadmap
        fields = [
            'id', 'title', 'target_role', 'skill_gap_summary',
            'estimated_duration', 'total_milestones', 'completed_milestones',
            'progress_percentage', 'is_active', 'created_at', 'updated_at',
            'stages'
        ]


class LearningRoadmapCreateSerializer(serializers.Serializer):
    target_role = serializers.CharField(max_length=200, required=False, allow_blank=True)
    experience_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced'],
        default='beginner'
    )
    weekly_hours = serializers.IntegerField(default=10, min_value=2, max_value=60)


class MilestoneToggleSerializer(serializers.Serializer):
    is_completed = serializers.BooleanField(required=False)


class LearningResourceSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)

    class Meta:
        model = LearningResource
        fields = [
            'id', 'title', 'category', 'resource_type', 'difficulty',
            'difficulty_display', 'url', 'description', 'is_free',
            'is_featured', 'created_at'
        ]


class ReportedContentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ReportedContent
        fields = [
            'id', 'category', 'category_display', 'subject', 'description',
            'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['status', 'status_display', 'created_at']
