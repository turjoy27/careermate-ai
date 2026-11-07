from rest_framework import serializers
from .models import CareerRecommendationSession, CareerRecommendation, SkillGapReport


class SkillGapReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapReport
        fields = [
            'id',
            'target_role',
            'match_percentage',
            'strengths',
            'critical_missing_skills',
            'learning_priority',
            'created_at',
        ]


class CareerRecommendationSerializer(serializers.ModelSerializer):
    skill_gap_report = SkillGapReportSerializer(read_only=True)

    class Meta:
        model = CareerRecommendation
        fields = [
            'id',
            'title',
            'match_score',
            'suitability_reason',
            'market_outlook_bd',
            'required_skills',
            'matched_skills',
            'missing_skills',
            'growth_potential',
            'recommended_next_steps',
            'skill_gap_report',
            'created_at',
        ]


class CareerRecommendationSessionSerializer(serializers.ModelSerializer):
    recommendations = CareerRecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = CareerRecommendationSession
        fields = [
            'id',
            'interests',
            'work_preference',
            'target_industries',
            'target_analysis',
            'readiness_level',
            'created_at',
            'recommendations',
        ]


class CareerRecommendationRequestSerializer(serializers.Serializer):
    interests = serializers.CharField(required=False, allow_blank=True, max_length=500)
    work_preference = serializers.CharField(required=False, allow_blank=True, max_length=100)
    target_industries = serializers.CharField(required=False, allow_blank=True, max_length=200)
