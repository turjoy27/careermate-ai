from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Education, UserProfile, UserSkill
from apps.ai_services.schemas import CareerRecommendationItem, CareerRecommendationResponse
from apps.careers.models import CareerRecommendation, CareerRecommendationSession, SkillGapReport
from apps.careers.services import CareerRecommendationService

User = get_user_model()


class CareerRecommendationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='student_rec@example.com',
            password='Password123!',
            first_name='Anik',
            last_name='Das',
            role='student'
        )
        self.profile = self.user.profile
        self.profile.target_career = 'Data Scientist'
        self.profile.save()

        Education.objects.create(
            profile=self.profile,
            institution='BUET',
            degree='B.Sc.',
            field_of_study='CSE',
            start_date='2020-01-01',
            is_current=True
        )
        UserSkill.objects.create(
            profile=self.profile,
            skill_name='Python',
            category='technical',
            proficiency='intermediate'
        )

        self.mock_ai_response = CareerRecommendationResponse(
            target_analysis='Promising background with strong Python base for data analytics roles.',
            readiness_level='Needs Foundational Upskilling',
            recommendations=[
                CareerRecommendationItem(
                    title='Junior Data Analyst',
                    match_score=82,
                    suitability_reason='Python skills and analytical mindset match modern data requirements.',
                    market_outlook_bd='Rising recruitment in telcos (Grameenphone, Robi) and fintech (bKash).',
                    required_skills=['Python', 'SQL', 'Pandas', 'PowerBI'],
                    matched_skills=['Python'],
                    missing_skills=['SQL', 'Pandas', 'PowerBI'],
                    growth_potential='High',
                    recommended_next_steps=['Master SQL queries', 'Build a dashboard in PowerBI']
                )
            ]
        )

    def test_empty_profile_raises_value_error(self):
        empty_user = User.objects.create_user(
            email='empty@example.com',
            password='Password123!'
        )
        with self.assertRaises(ValueError):
            CareerRecommendationService.generate_recommendations(empty_user.profile)

    def test_successful_recommendation_and_skill_gap_persistence(self):
        mock_ai_service = MagicMock()
        mock_ai_service.generate_career_recommendations.return_value = self.mock_ai_response

        session = CareerRecommendationService.generate_recommendations(
            profile=self.profile,
            preferences={'interests': 'Data Science & Machine Learning'},
            ai_service=mock_ai_service
        )

        # Check Session
        self.assertIsInstance(session, CareerRecommendationSession)
        self.assertEqual(session.profile, self.profile)
        self.assertEqual(session.readiness_level, 'Needs Foundational Upskilling')

        # Check Recommendations
        self.assertEqual(session.recommendations.count(), 1)
        rec = session.recommendations.first()
        self.assertEqual(rec.title, 'Junior Data Analyst')
        self.assertEqual(rec.match_score, 82)

        # Check Skill Gap Report
        self.assertTrue(hasattr(rec, 'skill_gap_report'))
        gap_report = rec.skill_gap_report
        self.assertEqual(gap_report.target_role, 'Junior Data Analyst')
        self.assertEqual(gap_report.match_percentage, 82)
        self.assertEqual(gap_report.strengths, ['Python'])
        self.assertIn('SQL', gap_report.critical_missing_skills)


class CareerWebViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='careerview@example.com',
            password='Password123!',
            first_name='Mitu',
            last_name='Akter'
        )
        self.profile = self.user.profile
        Education.objects.create(
            profile=self.profile,
            institution='NSU',
            degree='B.Sc.',
            field_of_study='ECE',
            start_date='2019-01-01',
            is_current=False
        )
        UserSkill.objects.create(
            profile=self.profile,
            skill_name='JavaScript',
            category='technical',
            proficiency='intermediate'
        )
        self.client.login(email='careerview@example.com', password='Password123!')

    def test_unauthenticated_access_redirects(self):
        anon_client = Client()
        response = anon_client.get(reverse('careers-recommendations'))
        self.assertEqual(response.status_code, 302)

    def test_recommendations_page_get_with_empty_and_filled_session(self):
        # Empty GET
        response = self.client.get(reverse('careers-recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Career Recommendations')

        # Create sample session
        session = CareerRecommendationSession.objects.create(
            profile=self.profile,
            target_analysis='Solid web development foundation.',
            readiness_level='Entry-Ready'
        )
        rec = CareerRecommendation.objects.create(
            session=session,
            profile=self.profile,
            title='Frontend Developer',
            match_score=85,
            suitability_reason='Strong JS abilities.',
            market_outlook_bd='Plentiful frontend job openings in Dhaka.',
            required_skills=['JavaScript', 'React', 'CSS'],
            matched_skills=['JavaScript'],
            missing_skills=['React'],
            growth_potential='High',
            recommended_next_steps=['Learn React hooks']
        )
        SkillGapReport.objects.create(
            recommendation=rec,
            profile=self.profile,
            target_role='Frontend Developer',
            match_percentage=85,
            strengths=['JavaScript'],
            critical_missing_skills=['React'],
            learning_priority=['React']
        )

        # Re-fetch GET
        response_filled = self.client.get(reverse('careers-recommendations'))
        self.assertEqual(response_filled.status_code, 200)
        self.assertContains(response_filled, 'Frontend Developer')
        self.assertContains(response_filled, '85%')

        # Detail View
        detail_response = self.client.get(reverse('careers-detail', kwargs={'pk': rec.id}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Skill-Gap Diagnostic')
        self.assertContains(detail_response, 'React')

        # History View
        history_response = self.client.get(reverse('careers-history'))
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, 'Frontend Developer')


class CareerAPITests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email='api_careers@example.com',
            password='Password123!',
            first_name='Sabbir',
            last_name='Khan'
        )
        self.profile = self.user.profile
        Education.objects.create(
            profile=self.profile,
            institution='IUT',
            degree='B.Sc.',
            field_of_study='CSE',
            start_date='2021-01-01',
            is_current=True
        )
        UserSkill.objects.create(
            profile=self.profile,
            skill_name='Python',
            category='technical',
            proficiency='expert'
        )

    def test_unauthenticated_api_recommend_forbidden(self):
        response = self.api_client.post(reverse('api-careers-recommend'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.careers.services.GeminiService')
    def test_authenticated_api_recommend_success(self, mock_gemini_class):
        mock_instance = MagicMock()
        mock_instance.generate_career_recommendations.return_value = CareerRecommendationResponse(
            target_analysis='Exceptional Python aptitude.',
            readiness_level='Entry-Ready',
            recommendations=[
                CareerRecommendationItem(
                    title='Python Backend Engineer',
                    match_score=90,
                    suitability_reason='Excellent match with Python expertise.',
                    market_outlook_bd='Thriving backend hiring market.',
                    required_skills=['Python', 'Django', 'FastAPI'],
                    matched_skills=['Python'],
                    missing_skills=['Django', 'FastAPI'],
                    growth_potential='High',
                    recommended_next_steps=['Study Django architecture']
                )
            ]
        )
        mock_gemini_class.return_value = mock_instance

        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            reverse('api-careers-recommend'),
            {'interests': 'Backend Systems'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['readiness_level'], 'Entry-Ready')
        self.assertEqual(len(response.data['recommendations']), 1)
        rec_id = response.data['recommendations'][0]['id']

        # Query skill-gap endpoint
        gap_res = self.api_client.get(reverse('api-careers-skill-gap', kwargs={'pk': rec_id}))
        self.assertEqual(gap_res.status_code, status.HTTP_200_OK)
        self.assertEqual(gap_res.data['target_role'], 'Python Backend Engineer')
        self.assertEqual(gap_res.data['match_percentage'], 90)
