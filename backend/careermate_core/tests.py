from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint_returns_200(self):
        url = reverse('api-health-check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('status'), 'healthy')
        self.assertEqual(response.data.get('version'), '1.0.0')
        self.assertIn('checks', response.data)
        self.assertEqual(response.data['checks']['database']['engine'], 'mysql')
        self.assertEqual(response.data['checks']['database']['status'], 'healthy')
        self.assertEqual(response.data['checks']['api']['status'], 'healthy')
