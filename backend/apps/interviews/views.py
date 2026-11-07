import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
from apps.ai_services.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIServiceError,
    AIUnavailableError,
)
from .models import InterviewQuestion, InterviewSession
from .serializers import (
    InterviewAnswerSubmitSerializer,
    InterviewQuestionSerializer,
    InterviewSessionSerializer,
    InterviewStartRequestSerializer,
)
from .services import InterviewService


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class InterviewSetupView(View):
    """Interview setup arena and historical practice sessions list."""
    template_name = 'interviews/setup.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        sessions = profile.interview_sessions.prefetch_related('questions').all()

        return render(request, self.template_name, {
            'profile': profile,
            'sessions': sessions,
            'default_role': profile.target_career or 'Software Engineer',
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        target_role = request.POST.get('target_role', '').strip() or profile.target_career or 'Software Engineer'
        difficulty = request.POST.get('difficulty', 'junior')
        question_type = request.POST.get('question_type', 'mixed')
        count = int(request.POST.get('count', 3))

        try:
            session = InterviewService.start_session(
                profile=profile,
                target_role=target_role,
                difficulty=difficulty,
                question_type=question_type,
                count=count
            )
            messages.success(
                request,
                f"Generated {session.questions.count()} calibrated interview questions for {session.target_role}!"
            )
            return redirect('interviews-session', session_id=session.id)
        except AIConfigurationError as e:
            messages.error(request, str(e))
        except AIRateLimitError as e:
            messages.error(request, str(e))
        except (AIServiceError, AIUnavailableError) as e:
            messages.error(request, f"AI generation error: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")

        return redirect('interviews-setup')


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class InterviewSessionView(View):
    """Interactive room for walking through questions, typing answers, and reviewing scores."""
    template_name = 'interviews/session.html'

    def get(self, request, session_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        session = get_object_or_404(
            InterviewSession.objects.prefetch_related('questions'),
            pk=session_id,
            profile=profile
        )

        questions = list(session.questions.all())
        q_order = int(request.GET.get('q', 1))
        # Ensure within range
        if q_order < 1 or q_order > len(questions):
            q_order = 1

        active_question = questions[q_order - 1] if questions else None

        return render(request, self.template_name, {
            'profile': profile,
            'session': session,
            'questions': questions,
            'active_question': active_question,
            'current_order': q_order,
            'has_next': q_order < len(questions),
            'has_prev': q_order > 1,
            'next_order': q_order + 1,
            'prev_order': q_order - 1,
        })


@login_required(login_url='accounts-login')
@require_POST
def submit_interview_answer(request, session_id, question_id):
    """Handles answer submission and invokes Gemini evaluation."""
    profile = get_object_or_404(UserProfile, user=request.user)
    session = get_object_or_404(InterviewSession, pk=session_id, profile=profile)
    question = get_object_or_404(InterviewQuestion, pk=question_id, session=session)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if is_ajax:
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            answer = data.get('answer', '')
        except Exception:
            answer = ''
    else:
        answer = request.POST.get('answer', '')

    try:
        updated_q = InterviewService.submit_and_evaluate_answer(question, answer)

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'question': InterviewQuestionSerializer(updated_q).data,
                'session_completed': session.is_completed,
                'overall_score': session.overall_score,
            })

        messages.success(request, f"Question {question.order} evaluated: Score {updated_q.score}/10!")
    except ValueError as val_err:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': str(val_err)}, status=400)
        messages.warning(request, str(val_err))
    except (AIConfigurationError, AIRateLimitError, AIServiceError, AIUnavailableError) as ai_err:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': str(ai_err)}, status=502)
        messages.error(request, f"Evaluation failed: {str(ai_err)}")
    except Exception as e:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        messages.error(request, f"Error: {str(e)}")

    return redirect(f"/interviews/{session.id}/?q={question.order}")


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class InterviewSummaryView(View):
    """Overall scorecard and feedback review after completing all questions."""
    template_name = 'interviews/summary.html'

    def get(self, request, session_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        session = get_object_or_404(
            InterviewSession.objects.prefetch_related('questions'),
            pk=session_id,
            profile=profile
        )

        return render(request, self.template_name, {
            'profile': profile,
            'session': session,
            'questions': session.questions.all(),
        })


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class InterviewSessionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        sessions = profile.interview_sessions.all()
        serializer = InterviewSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InterviewStartRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = serializer.validated_data

        try:
            session = InterviewService.start_session(
                profile=profile,
                target_role=data.get('target_role', ''),
                difficulty=data.get('difficulty', 'junior'),
                question_type=data.get('question_type', 'mixed'),
                count=data.get('count', 3)
            )
            return Response(InterviewSessionSerializer(session).data, status=status.HTTP_201_CREATED)
        except AIConfigurationError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIRateLimitError as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (AIServiceError, AIUnavailableError) as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class InterviewSessionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        session = get_object_or_404(InterviewSession, pk=session_id, profile=profile)
        serializer = InterviewSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewSubmitAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, question_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        session = get_object_or_404(InterviewSession, pk=session_id, profile=profile)
        question = get_object_or_404(InterviewQuestion, pk=question_id, session=session)

        serializer = InterviewAnswerSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        answer_text = serializer.validated_data['answer']
        try:
            updated_q = InterviewService.submit_and_evaluate_answer(question, answer_text)
            return Response({
                'question': InterviewQuestionSerializer(updated_q).data,
                'session_completed': session.is_completed,
                'overall_score': session.overall_score,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AIConfigurationError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIRateLimitError as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (AIServiceError, AIUnavailableError) as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
