from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from apps.ai_services.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseValidationError,
    AIServiceError,
    AIUnavailableError,
)
from .models import (
    LearningResource,
    LearningRoadmap,
    ReportedContent,
    RoadmapMilestone,
    RoadmapStage,
)
from .serializers import (
    LearningResourceSerializer,
    LearningRoadmapCreateSerializer,
    LearningRoadmapSerializer,
    MilestoneToggleSerializer,
    ReportedContentSerializer,
)
from .services import RoadmapService


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class RoadmapListView(View):
    """Lists candidate's saved roadmaps and displays curated learning library."""
    template_name = 'roadmaps/list.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        roadmaps = profile.roadmaps.prefetch_related('stages__milestones').all()

        # Category filter for curated platform resources
        category = request.GET.get('category', '').strip()
        resources_qs = LearningResource.objects.all()
        if category:
            resources_qs = resources_qs.filter(category__icontains=category)
        curated_resources = resources_qs[:12]

        categories = LearningResource.objects.values_list('category', flat=True).distinct()

        return render(request, self.template_name, {
            'profile': profile,
            'roadmaps': roadmaps,
            'curated_resources': curated_resources,
            'categories': categories,
            'selected_category': category,
            'default_role': profile.target_career or 'Full Stack Developer',
        })


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class RoadmapCreateView(View):
    """Interactive generator for a new personalized learning roadmap."""
    template_name = 'roadmaps/create.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {
            'profile': profile,
            'default_role': profile.target_career or 'Full Stack Python Developer',
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        target_role = request.POST.get('target_role', '').strip() or profile.target_career or 'Software Engineer'
        experience_level = request.POST.get('experience_level', 'beginner')
        try:
            weekly_hours = int(request.POST.get('weekly_hours', 10))
        except ValueError:
            weekly_hours = 10

        try:
            roadmap = RoadmapService.generate_roadmap(
                profile=profile,
                target_role=target_role,
                experience_level=experience_level,
                weekly_hours=weekly_hours
            )
            messages.success(request, f"Generated personalized learning roadmap for {roadmap.target_role}!")
            return redirect('roadmaps-detail', pk=roadmap.id)
        except AIConfigurationError as e:
            messages.error(request, str(e))
        except AIRateLimitError as e:
            messages.error(request, str(e))
        except (AIServiceError, AIUnavailableError, AIResponseValidationError) as e:
            messages.error(request, f"Roadmap generation failed: {str(e)}")

        return redirect('roadmaps-create')


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class RoadmapDetailView(View):
    """Detailed progressive 3-stage roadmap with interactive milestone checklist."""
    template_name = 'roadmaps/detail.html'

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        roadmap = get_object_or_404(
            LearningRoadmap.objects.prefetch_related('stages__milestones', 'stages__resources'),
            pk=pk,
            profile=profile
        )

        return render(request, self.template_name, {
            'profile': profile,
            'roadmap': roadmap,
            'stages': roadmap.stages.all(),
        })


@login_required(login_url='accounts-login')
def toggle_milestone_completion(request, pk):
    """AJAX endpoint to check or uncheck a learning milestone."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required.'}, status=405)

    profile = get_object_or_404(UserProfile, user=request.user)
    milestone = get_object_or_404(
        RoadmapMilestone.objects.select_related('stage__roadmap'),
        pk=pk,
        stage__roadmap__profile=profile
    )

    result = RoadmapService.toggle_milestone(milestone)
    return JsonResponse({'status': 'success', **result})


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ReportContentView(View):
    """User submission of feedback, content inaccuracy, or support ticket."""
    template_name = 'roadmaps/report.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        category = request.POST.get('category', 'general_feedback')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()

        if not subject or not description:
            messages.error(request, "Subject and detailed description are required.")
            return render(request, self.template_name)

        ReportedContent.objects.create(
            user=request.user,
            category=category,
            subject=subject,
            description=description
        )
        messages.success(request, "Thank you! Your feedback has been submitted to the administration team.")
        return redirect('dashboard-home')


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class RoadmapListCreateAPIView(APIView):
    """List candidate's roadmaps or generate a new roadmap."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        roadmaps = profile.roadmaps.prefetch_related('stages__milestones', 'stages__resources').all()
        serializer = LearningRoadmapSerializer(roadmaps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        in_serializer = LearningRoadmapCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)

        target_role = in_serializer.validated_data.get('target_role') or profile.target_career or 'Software Engineer'
        experience_level = in_serializer.validated_data.get('experience_level', 'beginner')
        weekly_hours = in_serializer.validated_data.get('weekly_hours', 10)

        try:
            roadmap = RoadmapService.generate_roadmap(
                profile=profile,
                target_role=target_role,
                experience_level=experience_level,
                weekly_hours=weekly_hours
            )
            out_serializer = LearningRoadmapSerializer(roadmap)
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        except (AIServiceError, AIUnavailableError, AIRateLimitError, AIConfigurationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RoadmapDetailAPIView(APIView):
    """Retrieve or archive a specific roadmap."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        roadmap = get_object_or_404(
            LearningRoadmap.objects.prefetch_related('stages__milestones', 'stages__resources'),
            pk=pk,
            profile=profile
        )
        serializer = LearningRoadmapSerializer(roadmap)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        roadmap = get_object_or_404(LearningRoadmap, pk=pk, profile=profile)
        roadmap.delete()
        return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)


class RoadmapMilestoneToggleAPIView(APIView):
    """Check or uncheck milestone completion via API."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        milestone = get_object_or_404(
            RoadmapMilestone.objects.select_related('stage__roadmap'),
            pk=pk,
            stage__roadmap__profile=profile
        )
        serializer = MilestoneToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_completed = serializer.validated_data.get('is_completed')

        result = RoadmapService.toggle_milestone(milestone, is_completed=is_completed)
        return Response(result, status=status.HTTP_200_OK)


class LearningResourceListAPIView(APIView):
    """Browse platform curated learning resources."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category')
        difficulty = request.query_params.get('difficulty')

        qs = LearningResource.objects.all()
        if category:
            qs = qs.filter(category__icontains=category)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)

        serializer = LearningResourceSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReportContentCreateAPIView(APIView):
    """Submit platform report / support ticket."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReportedContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
