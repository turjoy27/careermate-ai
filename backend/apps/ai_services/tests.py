from unittest.mock import MagicMock, patch
from django.test import TestCase
from apps.ai_services.client import GeminiService
from apps.ai_services.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseValidationError,
    AIUnavailableError,
)
from apps.ai_services.schemas import CareerRecommendationResponse


class GeminiServiceUnitTests(TestCase):
    def setUp(self):
        self.profile_sample = {
            'role': 'University Student',
            'headline': 'CS Senior',
            'target_career': 'Backend Engineer',
            'summary': 'Enthusiastic Python programmer',
            'city': 'Dhaka',
            'country': 'Bangladesh',
            'educations': [{'institution': 'DU', 'degree': 'B.Sc.', 'field_of_study': 'CSE', 'is_current': True}],
            'skills': [{'skill_name': 'Python', 'category': 'technical', 'proficiency': 'intermediate'}],
            'experiences': []
        }

    def test_missing_api_key_raises_configuration_error(self):
        service = GeminiService(api_key="")
        with self.assertRaises(AIConfigurationError):
            service.generate_career_recommendations(self.profile_sample)

    @patch('apps.ai_services.client.genai.Client')
    def test_valid_structured_ai_response(self, mock_genai_client_class):
        valid_json = """{
            "target_analysis": "Strong computational fundamentals with immediate readiness for junior Python backend roles.",
            "readiness_level": "Entry-Ready",
            "recommendations": [
                {
                    "title": "Django Backend Developer",
                    "match_score": 88,
                    "suitability_reason": "Solid Python proficiency and computer science degree directly align with Django requirements.",
                    "market_outlook_bd": "High demand in Dhaka software export companies and local fintech applications.",
                    "required_skills": ["Python", "Django", "MySQL", "REST APIs", "Docker"],
                    "matched_skills": ["Python"],
                    "missing_skills": ["Django", "MySQL", "Docker"],
                    "growth_potential": "High",
                    "recommended_next_steps": [
                        "Build an end-to-end CRUD project using Django and MySQL",
                        "Learn Docker basics for local containerization"
                    ]
                }
            ]
        }"""
        mock_response = MagicMock()
        mock_response.text = valid_json

        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = mock_response
        mock_genai_client_class.return_value = mock_instance

        service = GeminiService(api_key="valid-test-key")
        result = service.generate_career_recommendations(self.profile_sample)

        self.assertIsInstance(result, CareerRecommendationResponse)
        self.assertEqual(result.readiness_level, "Entry-Ready")
        self.assertEqual(len(result.recommendations), 1)
        rec = result.recommendations[0]
        self.assertEqual(rec.title, "Django Backend Developer")
        self.assertEqual(rec.match_score, 88)
        self.assertIn("Docker", rec.missing_skills)

    @patch('apps.ai_services.client.genai.Client')
    def test_malformed_json_response_raises_validation_error(self, mock_genai_client_class):
        mock_response = MagicMock()
        mock_response.text = '{"target_analysis": "broken json without closing brackets'

        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = mock_response
        mock_genai_client_class.return_value = mock_instance

        service = GeminiService(api_key="valid-test-key")
        with self.assertRaises(AIResponseValidationError):
            service.generate_career_recommendations(self.profile_sample)

    @patch('apps.ai_services.client.genai.Client')
    def test_invalid_schema_response_raises_validation_error(self, mock_genai_client_class):
        # Valid JSON but missing required fields defined in CareerRecommendationResponse
        mock_response = MagicMock()
        mock_response.text = '{"some_unrelated_field": "test", "recommendations": []}'

        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = mock_response
        mock_genai_client_class.return_value = mock_instance

        service = GeminiService(api_key="valid-test-key")
        with self.assertRaises(AIResponseValidationError):
            service.generate_career_recommendations(self.profile_sample)

    @patch('apps.ai_services.client.genai.Client')
    def test_rate_limit_429_raises_rate_limit_exception(self, mock_genai_client_class):
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        mock_genai_client_class.return_value = mock_instance

        service = GeminiService(api_key="valid-test-key")
        with self.assertRaises(AIRateLimitError):
            service.generate_career_recommendations(self.profile_sample)

    @patch('apps.ai_services.client.genai.Client')
    def test_unavailable_network_error_raises_unavailable_exception(self, mock_genai_client_class):
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("Connection refused: Service unavailable")
        mock_genai_client_class.return_value = mock_instance

        service = GeminiService(api_key="valid-test-key")
        with self.assertRaises(AIUnavailableError):
            service.generate_career_recommendations(self.profile_sample)
