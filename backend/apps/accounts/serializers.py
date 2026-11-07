from rest_framework import serializers
from .models import User, UserProfile, Education, Experience, UserSkill


class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = ['id', 'skill_name', 'category', 'proficiency']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'is_current', 'grade']


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'company', 'position', 'location', 'start_date', 'end_date', 'is_current', 'description']


class UserProfileSerializer(serializers.ModelSerializer):
    skills = UserSkillSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user_email',
            'full_name',
            'role',
            'headline',
            'phone',
            'city',
            'country',
            'summary',
            'target_career',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'skills',
            'educations',
            'experiences',
            'updated_at',
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)
