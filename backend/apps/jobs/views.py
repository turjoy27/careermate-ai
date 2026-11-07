from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from .matching import JobMatchEngine
from .models import JobListing, SavedJob
from .serializers import JobListingSerializer, SavedJobSerializer


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class JobListView(View):
    """Job search & matching portal with algorithmic compatibility scores."""
    template_name = 'jobs/list.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        query = request.GET.get('q', '').strip()
        job_type = request.GET.get('job_type', '').strip()
        experience_level = request.GET.get('experience_level', '').strip()
        workplace_type = request.GET.get('workplace_type', '').strip()
        min_match = request.GET.get('min_match', '').strip()

        jobs_qs = JobListing.objects.filter(is_active=True)

        if query:
            jobs_qs = jobs_qs.filter(
                Q(title__icontains=query) |
                Q(company_name__icontains=query) |
                Q(description__icontains=query) |
                Q(required_skills_raw__icontains=query)
            )

        if job_type:
            jobs_qs = jobs_qs.filter(job_type=job_type)

        if experience_level:
            jobs_qs = jobs_qs.filter(experience_level=experience_level)

        if workplace_type:
            jobs_qs = jobs_qs.filter(workplace_type=workplace_type)

        # Calculate algorithmic match data for each job
        saved_job_ids = set(profile.saved_jobs.values_list('job_id', flat=True))

        matched_jobs = []
        for job in jobs_qs:
            fit = JobMatchEngine.evaluate_fit(profile, job)
            score = fit['match_score']

            if min_match and min_match.isdigit():
                if score < int(min_match):
                    continue

            matched_jobs.append({
                'job': job,
                'match_score': score,
                'matched_required': fit['matched_required'],
                'missing_required': fit['missing_required'],
                'matched_preferred': fit['matched_preferred'],
                'breakdown_reason': fit['breakdown_reason'],
                'is_saved': job.id in saved_job_ids,
            })

        # Sort jobs by match score descending
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)

        return render(request, self.template_name, {
            'profile': profile,
            'matched_jobs': matched_jobs,
            'total_count': len(matched_jobs),
            'filters': {
                'q': query,
                'job_type': job_type,
                'experience_level': experience_level,
                'workplace_type': workplace_type,
                'min_match': min_match,
            }
        })


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class JobDetailView(View):
    """Detailed job description and transparent skill-fit diagnostic."""
    template_name = 'jobs/detail.html'

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        job = get_object_or_404(JobListing, pk=pk, is_active=True)

        fit = JobMatchEngine.evaluate_fit(profile, job)
        is_saved = SavedJob.objects.filter(profile=profile, job=job).exists()

        return render(request, self.template_name, {
            'profile': profile,
            'job': job,
            'fit': fit,
            'is_saved': is_saved,
        })


@login_required(login_url='accounts-login')
@require_POST
def toggle_save_job(request, pk):
    """Toggles bookmark status of a job listing."""
    profile = get_object_or_404(UserProfile, user=request.user)
    job = get_object_or_404(JobListing, pk=pk)

    saved_item = SavedJob.objects.filter(profile=profile, job=job).first()
    if saved_item:
        saved_item.delete()
        is_saved = False
        msg = f"Job '{job.title}' removed from saved jobs."
    else:
        SavedJob.objects.create(profile=profile, job=job)
        is_saved = True
        msg = f"Job '{job.title}' saved to bookmarks."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'success', 'is_saved': is_saved, 'message': msg})

    messages.info(request, msg)
    return redirect('jobs-detail', pk=job.id)


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class SavedJobsListView(View):
    """Lists all bookmarked jobs for the user."""
    template_name = 'jobs/saved_list.html'

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        saved_entries = profile.saved_jobs.select_related('job').filter(job__is_active=True)

        saved_with_fit = []
        for entry in saved_entries:
            fit = JobMatchEngine.evaluate_fit(profile, entry.job)
            saved_with_fit.append({
                'entry': entry,
                'job': entry.job,
                'match_score': fit['match_score'],
                'matched_required': fit['matched_required'],
                'missing_required': fit['missing_required'],
            })

        return render(request, self.template_name, {
            'profile': profile,
            'saved_jobs': saved_with_fit,
        })


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class JobListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = JobListing.objects.filter(is_active=True)
        serializer = JobListingSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        job = get_object_or_404(JobListing, pk=pk, is_active=True)
        serializer = JobListingSerializer(job, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobSaveToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        job = get_object_or_404(JobListing, pk=pk)

        saved_item = SavedJob.objects.filter(profile=profile, job=job).first()
        if saved_item:
            saved_item.delete()
            return Response({'status': 'removed', 'is_saved': False}, status=status.HTTP_200_OK)
        else:
            SavedJob.objects.create(profile=profile, job=job)
            return Response({'status': 'saved', 'is_saved': True}, status=status.HTTP_201_CREATED)


class SavedJobsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        saved = profile.saved_jobs.all()
        serializer = SavedJobSerializer(saved, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
