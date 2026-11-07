from rest_framework import serializers
from .models import Resume, ResumeEducation, ResumeExperience, ResumeProject


class ResumeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeEducation
        fields = ['id', 'institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'grade', 'order']


class ResumeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeExperience
        fields = ['id', 'company', 'position', 'location', 'start_date', 'end_date', 'description', 'order']


class ResumeProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeProject
        fields = ['id', 'title', 'tech_stack', 'live_link', 'github_link', 'description', 'order']


class ResumeSerializer(serializers.ModelSerializer):
    educations = ResumeEducationSerializer(many=True, read_only=True)
    experiences = ResumeExperienceSerializer(many=True, read_only=True)
    projects = ResumeProjectSerializer(many=True, read_only=True)
    skills_list = serializers.ListField(read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id',
            'title',
            'target_role',
            'full_name',
            'email',
            'phone',
            'location',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'professional_summary',
            'skills_raw',
            'skills_list',
            'template_style',
            'educations',
            'experiences',
            'projects',
            'created_at',
            'updated_at',
        ]
