from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
from .models import CareerRecommendation, CareerRecommendationSession, SkillGapReport
from .serializers import (
    CareerRecommendationRequestSerializer,
    CareerRecommendationSerializer,
    CareerRecommendationSessionSerializer,
    SkillGapReportSerializer,
)
from .services import CareerRecommendationService


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class CareerRecommendationsView(View):
    """Primary page for viewing and generating AI career recommendations."""
    template_name = 'careers/recommendations.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        latest_session = profile.career_sessions.prefetch_related('recommendations').first()

        context = {
            'profile': profile,
            'latest_session': latest_session,
            'recommendations': latest_session.recommendations.all() if latest_session else [],
            'has_minimum_profile': profile.skills.exists() or profile.educations.exists(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        interests = request.POST.get('interests', '').strip()
        work_preference = request.POST.get('work_preference', '').strip()
        target_industries = request.POST.get('target_industries', '').strip()

        preferences = {
            'interests': interests,
            'work_preference': work_preference,
            'target_industries': target_industries,
        }

        try:
            session = CareerRecommendationService.generate_recommendations(profile, preferences)
            messages.success(
                request,
                f"Generated {session.recommendations.count()} AI career paths matched to your background!"
            )
        except ValueError as val_err:
            messages.warning(request, str(val_err))
        except AIConfigurationError:
            messages.error(
                request,
                "Gemini AI API key is not configured. Please contact the administrator or add GEMINI_API_KEY in .env."
            )
        except AIRateLimitError:
            messages.error(
                request,
                "AI rate limit reached. Please wait a minute before requesting another recommendation."
            )
        except (AIResponseValidationError, AIUnavailableError, AIServiceError) as ai_err:
            messages.error(request, f"AI generation error: {str(ai_err)}")

        return redirect('careers-recommendations')


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class CareerDetailView(View):
    """In-depth view of a specific career recommendation and its skill-gap report."""
    template_name = 'careers/detail.html'

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        recommendation = get_object_or_404(
            CareerRecommendation.objects.select_related('skill_gap_report', 'session'),
            pk=pk,
            profile=profile
        )
        return render(request, self.template_name, {
            'profile': profile,
            'rec': recommendation,
            'gap_report': getattr(recommendation, 'skill_gap_report', None),
        })


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class CareerHistoryView(View):
    """Historical timeline of previous career recommendation sessions."""
    template_name = 'careers/history.html'

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        sessions = profile.career_sessions.prefetch_related('recommendations').all()
        return render(request, self.template_name, {
            'profile': profile,
            'sessions': sessions,
        })


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class CareerRecommendAPIView(APIView):
    """API endpoint to trigger Gemini career recommendation."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CareerRecommendationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        try:
            session = CareerRecommendationService.generate_recommendations(
                profile=profile,
                preferences=serializer.validated_data
            )
            response_serializer = CareerRecommendationSessionSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AIConfigurationError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIRateLimitError as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (AIResponseValidationError, AIUnavailableError, AIServiceError) as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class CareerHistoryAPIView(APIView):
    """API endpoint to list historical career recommendation sessions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        sessions = profile.career_sessions.all()
        serializer = CareerRecommendationSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CareerDetailAPIView(APIView):
    """API endpoint to get a single recommendation by ID."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        recommendation = get_object_or_404(CareerRecommendation, pk=pk, profile=profile)
        serializer = CareerRecommendationSerializer(recommendation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SkillGapAPIView(APIView):
    """API endpoint to get the skill-gap report for a specific recommendation."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        recommendation = get_object_or_404(CareerRecommendation, pk=pk, profile=profile)
        gap_report = get_object_or_404(SkillGapReport, recommendation=recommendation)
        serializer = SkillGapReportSerializer(gap_report)
        return Response(serializer.data, status=status.HTTP_200_OK)
