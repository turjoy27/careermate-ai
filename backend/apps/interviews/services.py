"""
Service layer orchestrating mock interview sessions and answer evaluations.
"""

from django.db import transaction
from django.utils import timezone
from apps.accounts.models import UserProfile
from apps.ai_services.client import GeminiService
from .models import InterviewQuestion, InterviewSession


class InterviewService:
    """Manages interview simulation workflows and answer evaluations."""

    @classmethod
    def start_session(
        cls,
        profile: UserProfile,
        target_role: str,
        difficulty: str = 'junior',
        question_type: str = 'mixed',
        count: int = 3,
        ai_service: GeminiService = None
    ) -> InterviewSession:
        """
        Generates calibrated questions using Gemini and records a new interview session in MySQL.
        """
        clean_role = target_role.strip() or profile.target_career or "Software Engineer"
        user_skills = [s.skill_name for s in profile.skills.all()]

        service = ai_service or GeminiService()
        ai_response = service.generate_interview_questions(
            target_role=clean_role,
            difficulty=difficulty,
            question_type=question_type,
            user_skills=user_skills,
            count=count
        )

        with transaction.atomic():
            session = InterviewSession.objects.create(
                profile=profile,
                target_role=clean_role,
                difficulty=difficulty,
                question_type=question_type,
                total_questions=len(ai_response.questions)
            )

            for idx, q in enumerate(ai_response.questions, start=1):
                InterviewQuestion.objects.create(
                    session=session,
                    order=idx,
                    category=q.category,
                    question_text=q.question_text,
                    intent_explanation=q.intent_explanation,
                    sample_approach=q.sample_approach
                )

        return session

    @classmethod
    def submit_and_evaluate_answer(
        cls,
        question: InterviewQuestion,
        user_answer: str,
        ai_service: GeminiService = None
    ) -> InterviewQuestion:
        """
        Submits candidate answer to Gemini, records rubric scoring, and updates session completion.
        """
        clean_answer = user_answer.strip()
        if not clean_answer:
            raise ValueError("Your answer cannot be empty. Please type or outline your response.")

        if len(clean_answer) < 10:
            raise ValueError("Please provide a more detailed response (minimum 10 characters).")

        service = ai_service or GeminiService()
        session = question.session

        evaluation = service.evaluate_interview_answer(
            question_text=question.question_text,
            user_answer=clean_answer,
            target_role=session.target_role,
            category=question.category
        )

        with transaction.atomic():
            question.user_answer = clean_answer
            question.score = evaluation.score
            question.feedback_summary = evaluation.feedback_summary
            question.strengths = evaluation.strengths
            question.areas_for_improvement = evaluation.areas_for_improvement
            question.ideal_points = evaluation.ideal_answer_points
            question.evaluated_at = timezone.now()
            question.save()

            # Check if all questions in this session have been scored
            all_questions = session.questions.all()
            scored_questions = [q for q in all_questions if q.score is not None]

            if len(scored_questions) == len(all_questions) and len(all_questions) > 0:
                avg_score = round(sum(q.score for q in scored_questions) / len(scored_questions), 1)
                session.overall_score = avg_score
                session.is_completed = True
                session.completed_at = timezone.now()
                session.save(update_fields=['overall_score', 'is_completed', 'completed_at'])

        return question
