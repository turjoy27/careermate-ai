from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai_services.schemas import (
    InterviewQuestionsResponse,
    GeneratedInterviewQuestion,
    AnswerEvaluationResponse
)
from apps.interviews.models import InterviewSession, InterviewQuestion
from apps.interviews.services import InterviewService


class InterviewServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="StrongPassword123!",
            first_name="Farhan",
            last_name="Kabir"
        )
        self.profile = self.user.profile
        self.profile.target_career = "Full Stack Engineer"
        self.profile.save()

    @patch("apps.ai_services.client.GeminiService.generate_interview_questions")
    def test_start_session(self, mock_generate):
        mock_generate.return_value = InterviewQuestionsResponse(
            role_title="Full Stack Engineer",
            difficulty_level="junior",
            questions=[
                GeneratedInterviewQuestion(
                    question_text="Explain the difference between SQL and NoSQL databases.",
                    category="technical",
                    intent_explanation="Assesses data modeling knowledge.",
                    sample_approach="Contrast schema flexibility with relational integrity."
                ),
                GeneratedInterviewQuestion(
                    question_text="Describe a time when you had to resolve a merge conflict in Git.",
                    category="behavioral",
                    intent_explanation="Assesses version control competency.",
                    sample_approach="Use the STAR method."
                )
            ]
        )

        session = InterviewService.start_session(
            profile=self.profile,
            target_role="Full Stack Engineer",
            difficulty="junior",
            question_type="mixed",
            count=2
        )

        self.assertEqual(session.profile, self.profile)
        self.assertEqual(session.target_role, "Full Stack Engineer")
        self.assertEqual(session.total_questions, 2)
        self.assertFalse(session.is_completed)
        self.assertEqual(session.questions.count(), 2)

        q1 = session.questions.first()
        self.assertEqual(q1.category, "technical")
        self.assertIn("SQL", q1.question_text)

    def test_submit_short_answer_raises_validation_error(self):
        session = InterviewSession.objects.create(
            profile=self.profile,
            target_role="DevOps Engineer",
            total_questions=1
        )
        question = InterviewQuestion.objects.create(
            session=session,
            order=1,
            category="technical",
            question_text="What is CI/CD?"
        )

        with self.assertRaises(ValueError):
            InterviewService.submit_and_evaluate_answer(question, "Too short")

    @patch("apps.ai_services.client.GeminiService.evaluate_interview_answer")
    def test_submit_and_evaluate_answer_and_complete_session(self, mock_eval):
        mock_eval.return_value = AnswerEvaluationResponse(
            score=8,
            strengths=["Clear explanation of pipelines", "Mentioned automated tests"],
            areas_for_improvement=["Could mention blue-green deployment strategies"],
            feedback_summary="Strong practical answer demonstrating foundational DevOps concepts.",
            ideal_answer_points=["Automated build", "Automated testing", "Continuous deployment triggers"]
        )

        session = InterviewSession.objects.create(
            profile=self.profile,
            target_role="DevOps Engineer",
            total_questions=1
        )
        question = InterviewQuestion.objects.create(
            session=session,
            order=1,
            category="technical",
            question_text="What is CI/CD and why is it important in software delivery?"
        )

        evaluated = InterviewService.submit_and_evaluate_answer(
            question=question,
            user_answer="CI/CD stands for Continuous Integration and Continuous Delivery. It automates testing and deployment."
        )

        self.assertEqual(evaluated.score, 8)
        self.assertEqual(len(evaluated.strengths), 2)
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        self.assertEqual(session.overall_score, 8.0)


class InterviewViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword123!",
            first_name="Sultana",
            last_name="Razia"
        )
        self.profile = self.user.profile

    def test_unauthenticated_access_redirects(self):
        resp = self.client.get(reverse('interviews-setup'))
        self.assertEqual(resp.status_code, 302)

    def test_setup_view_get(self):
        self.client.login(email="user@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('interviews-setup'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'interviews/setup.html')

    @patch("apps.interviews.services.InterviewService.start_session")
    def test_setup_view_post_starts_session(self, mock_start):
        session = InterviewSession.objects.create(
            profile=self.profile,
            target_role="Frontend Developer",
            total_questions=1
        )
        mock_start.return_value = session

        self.client.login(email="user@example.com", password="StrongPassword123!")
        resp = self.client.post(reverse('interviews-setup'), {
            'target_role': 'Frontend Developer',
            'difficulty': 'junior',
            'question_type': 'technical',
            'count': 3
        })
        self.assertRedirects(resp, reverse('interviews-session', kwargs={'session_id': session.id}))

    def test_session_view(self):
        session = InterviewSession.objects.create(
            profile=self.profile,
            target_role="Frontend Developer",
            total_questions=1
        )
        InterviewQuestion.objects.create(
            session=session,
            order=1,
            category="technical",
            question_text="Explain CSS Flexbox vs Grid."
        )
        self.client.login(email="user@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('interviews-session', kwargs={'session_id': session.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'interviews/session.html')
        self.assertContains(resp, "CSS Flexbox vs Grid")


class InterviewAPITestCase(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email="interviewapi@example.com",
            password="StrongPassword123!",
            first_name="API",
            last_name="User"
        )
        self.profile = self.user.profile
        self.session = InterviewSession.objects.create(
            profile=self.profile,
            target_role="Cloud Engineer",
            total_questions=1
        )
        self.question = InterviewQuestion.objects.create(
            session=self.session,
            order=1,
            category="technical",
            question_text="What is horizontal vs vertical scaling?"
        )

    def test_list_sessions_authenticated(self):
        self.api_client.force_authenticate(user=self.user)
        resp = self.api_client.get(reverse('api-interviews-list-create'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['target_role'], "Cloud Engineer")

    @patch("apps.interviews.services.InterviewService.submit_and_evaluate_answer")
    def test_api_submit_answer(self, mock_eval):
        self.question.score = 9
        self.question.feedback_summary = "Excellent answer"
        self.question.save()
        mock_eval.return_value = self.question

        self.api_client.force_authenticate(user=self.user)
        url = reverse('api-interviews-submit-answer', kwargs={
            'session_id': self.session.id,
            'question_id': self.question.id
        })
        resp = self.api_client.post(url, {
            'answer': 'Horizontal scaling adds more machines, whereas vertical scaling adds more CPU/RAM to an existing machine.'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['question']['score'], 9)
