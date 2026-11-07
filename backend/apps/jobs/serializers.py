from rest_framework import serializers
from .matching import JobMatchEngine
from .models import JobListing, SavedJob


class JobListingSerializer(serializers.ModelSerializer):
    match_data = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            'id',
            'title',
            'company_name',
            'company_logo_url',
            'location',
            'job_type',
            'workplace_type',
            'experience_level',
            'salary_range',
            'description',
            'responsibilities',
            'requirements',
            'required_skills_list',
            'preferred_skills_list',
            'apply_url',
            'apply_email',
            'is_saved',
            'match_data',
            'created_at',
        ]

    def get_match_data(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'profile'):
            return JobMatchEngine.evaluate_fit(request.user.profile, obj)
        return None

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'profile'):
            return SavedJob.objects.filter(profile=request.user.profile, job=obj).exists()
        return False


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ['id', 'job', 'notes', 'saved_at']
