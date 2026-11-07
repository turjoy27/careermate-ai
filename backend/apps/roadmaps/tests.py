from unittest.mock import patch
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, UserProfile, UserSkill
from apps.ai_services.schemas import (
    LearningRoadmapResponse,
    RoadmapMilestoneItem,
    RoadmapResourceItem,
    RoadmapStageItem,
)
from apps.roadmaps.models import (
    LearningResource,
    LearningRoadmap,
    ReportedContent,
    RoadmapMilestone,
    RoadmapResource,
    RoadmapStage,
)
from apps.roadmaps.services import RoadmapService


class RoadmapModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@example.com",
            password="StrongPassword123!",
            first_name="Tariq",
            last_name="Zia"
        )
        self.profile = self.user.profile
        self.roadmap = LearningRoadmap.objects.create(
            profile=self.profile,
            title="Backend Python Developer Roadmap",
            target_role="Backend Python Developer",
            skill_gap_summary="Needs to learn Django ORM, REST APIs, and Docker.",
            estimated_duration="16 Weeks"
        )
        self.stage = RoadmapStage.objects.create(
            roadmap=self.roadmap,
            stage_level="beginner",
            title="Stage 1: Python Core Foundations",
            order=1,
            duration_weeks="4 Weeks"
        )
        self.m1 = RoadmapMilestone.objects.create(
            stage=self.stage,
            title="Master Python Data Structures",
            order=1,
            is_completed=False
        )
        self.m2 = RoadmapMilestone.objects.create(
            stage=self.stage,
            title="Object-Oriented Programming & Exceptions",
            order=2,
            is_completed=False
        )

    def test_recalculate_progress(self):
        # Initial state: 0 / 2 = 0%
        self.roadmap.recalculate_progress()
        self.assertEqual(self.roadmap.progress_percentage, 0)
        self.assertEqual(self.roadmap.total_milestones, 2)
        self.assertEqual(self.roadmap.completed_milestones, 0)

        # Complete 1 milestone: 1 / 2 = 50%
        self.m1.is_completed = True
        self.m1.save()
        pct = self.roadmap.recalculate_progress()
        self.assertEqual(pct, 50)
        self.assertEqual(self.roadmap.completed_milestones, 1)

        # Complete second milestone: 2 / 2 = 100%
        self.m2.is_completed = True
        self.m2.save()
        pct2 = self.roadmap.recalculate_progress()
        self.assertEqual(pct2, 100)

    def test_learning_resource_model(self):
        res = LearningResource.objects.create(
            title="Official Python Tutorial",
            category="Python",
            resource_type="documentation",
            difficulty="beginner",
            url="https://docs.python.org/3/tutorial/",
            is_free=True
        )
        self.assertIn("Official Python Tutorial", str(res))

    def test_reported_content_model(self):
        report = ReportedContent.objects.create(
            user=self.user,
            category="general_feedback",
            subject="Great platform",
            description="Antigravity integration works nicely."
        )
        self.assertEqual(report.status, "pending")
        self.assertIn("Great platform", str(report))


class RoadmapServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="service_test@example.com",
            password="StrongPassword123!",
            first_name="Anisur",
            last_name="Rahman"
        )
        self.profile = self.user.profile
        UserSkill.objects.create(profile=self.profile, skill_name="Python", proficiency="intermediate")

    @patch("apps.ai_services.client.GeminiService.generate_learning_roadmap")
    def test_generate_roadmap_service(self, mock_ai):
        mock_ai.return_value = LearningRoadmapResponse(
            target_role="Full-Stack Django Developer",
            estimated_total_duration="14 Weeks (10 hrs/week)",
            skill_gap_summary="Strong Python fundamentals. Needs frontend integration and deployment skills.",
            stages=[
                RoadmapStageItem(
                    stage_level="beginner",
                    title="Stage 1: Advanced Python & Django Core",
                    duration_weeks="4 Weeks",
                    description="Deep dive into Django MVT and ORM.",
                    milestones=[
                        RoadmapMilestoneItem(
                            title="Build a multi-model CRUD application in Django",
                            skills_covered=["Django ORM", "Template inheritance"],
                            practical_task="Build a simple library inventory management system."
                        )
                    ],
                    recommended_resources=[
                        RoadmapResourceItem(
                            title="Django Official Docs",
                            resource_type="documentation",
                            url="https://docs.djangoproject.com",
                            is_free=True
                        )
                    ]
                ),
                RoadmapStageItem(
                    stage_level="intermediate",
                    title="Stage 2: REST APIs & Authentication",
                    duration_weeks="5 Weeks",
                    description="Building production RESTful services.",
                    milestones=[
                        RoadmapMilestoneItem(
                            title="Implement JWT token auth and rate limiting",
                            skills_covered=["DRF", "JWT", "Permissions"],
                            practical_task="Build a secure REST API for task tracking."
                        )
                    ],
                    recommended_resources=[]
                ),
                RoadmapStageItem(
                    stage_level="advanced",
                    title="Stage 3: Cloud Deployment & DevOps",
                    duration_weeks="5 Weeks",
                    description="Docker, CI/CD, and MySQL database optimization.",
                    milestones=[
                        RoadmapMilestoneItem(
                            title="Containerize with Docker and run MySQL in production",
                            skills_covered=["Docker", "Nginx", "MySQL optimization"],
                            practical_task="Deploy application on a VPS."
                        )
                    ],
                    recommended_resources=[]
                ),
            ]
        )

        roadmap = RoadmapService.generate_roadmap(
            profile=self.profile,
            target_role="Full-Stack Django Developer",
            experience_level="beginner",
            weekly_hours=10
        )

        self.assertEqual(roadmap.profile, self.profile)
        self.assertEqual(roadmap.target_role, "Full-Stack Django Developer")
        self.assertEqual(roadmap.stages.count(), 3)
        self.assertEqual(roadmap.total_milestones, 3)
        self.assertEqual(roadmap.progress_percentage, 0)

        # Test toggle milestone via service
        m1 = RoadmapMilestone.objects.filter(stage__roadmap=roadmap).first()
        result = RoadmapService.toggle_milestone(m1, is_completed=True)
        self.assertTrue(result['is_completed'])
        self.assertEqual(result['roadmap_completed'], 1)
        self.assertEqual(result['roadmap_progress_percentage'], 33)


class RoadmapWebViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="webuser@example.com",
            password="StrongPassword123!",
            first_name="Sadia",
            last_name="Afrin"
        )
        self.profile = self.user.profile
        self.roadmap = LearningRoadmap.objects.create(
            profile=self.profile,
            title="DevOps Engineer Roadmap",
            target_role="DevOps Engineer"
        )
        self.stage = RoadmapStage.objects.create(
            roadmap=self.roadmap,
            stage_level="beginner",
            title="Linux & Git",
            order=1
        )
        self.milestone = RoadmapMilestone.objects.create(
            stage=self.stage,
            title="Linux Server Admin Basics",
            order=1
        )

        # Other user for privacy test
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Candidate"
        )

    def test_unauthenticated_access_redirects(self):
        resp = self.client.get(reverse('roadmaps-list'))
        self.assertEqual(resp.status_code, 302)

    def test_list_view_authenticated(self):
        self.client.login(email="webuser@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('roadmaps-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'roadmaps/list.html')
        self.assertContains(resp, "DevOps Engineer")

    def test_detail_view_privacy_enforcement(self):
        # Other user cannot view webuser's roadmap -> 404
        self.client.login(email="other@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('roadmaps-detail', kwargs={'pk': self.roadmap.id}))
        self.assertEqual(resp.status_code, 404)

        # Owner can view roadmap -> 200
        self.client.login(email="webuser@example.com", password="StrongPassword123!")
        resp2 = self.client.get(reverse('roadmaps-detail', kwargs={'pk': self.roadmap.id}))
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, "Linux Server Admin Basics")

    def test_toggle_milestone_ajax(self):
        self.client.login(email="webuser@example.com", password="StrongPassword123!")
        url = reverse('milestone-toggle', kwargs={'pk': self.milestone.id})
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['roadmap_progress_percentage'], 100)

    def test_report_content_view(self):
        self.client.login(email="webuser@example.com", password="StrongPassword123!")
        url = reverse('report-content')
        resp = self.client.post(url, {
            'category': 'ai_inaccuracy',
            'subject': 'Inaccurate stage timing',
            'description': 'Stage 1 should allocate more time for Docker networking.'
        })
        self.assertRedirects(resp, reverse('dashboard-home'))
        self.assertTrue(ReportedContent.objects.filter(subject="Inaccurate stage timing").exists())


class AdminAnalyticsPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPassword123!",
            first_name="Regular",
            last_name="Student",
            role="student",
            is_staff=False
        )
        self.admin = User.objects.create_superuser(
            email="superadmin@careermate.ai",
            password="AdminPassword123!",
            first_name="Platform",
            last_name="SuperAdmin"
        )

    def test_student_forbidden_from_admin_analytics(self):
        self.client.login(email="student@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('admin-analytics'))
        self.assertEqual(resp.status_code, 403)

    def test_admin_authorized_for_analytics(self):
        self.client.login(email="superadmin@careermate.ai", password="AdminPassword123!")
        resp = self.client.get(reverse('admin-analytics'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'dashboard/admin_analytics.html')
        self.assertContains(resp, "Platform Administration & Analytics")


class RoadmapAPITestCase(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email="apiuser@example.com",
            password="StrongPassword123!",
            first_name="API",
            last_name="Dev"
        )
        self.profile = self.user.profile
        self.roadmap = LearningRoadmap.objects.create(
            profile=self.profile,
            title="QA Automation Roadmap",
            target_role="QA Automation Engineer"
        )
        self.stage = RoadmapStage.objects.create(
            roadmap=self.roadmap,
            stage_level="beginner",
            title="Selenium & PyTest",
            order=1
        )
        self.milestone = RoadmapMilestone.objects.create(
            stage=self.stage,
            title="Write first PyTest suite",
            order=1
        )

    def test_api_list_roadmaps(self):
        self.api_client.force_authenticate(user=self.user)
        resp = self.api_client.get(reverse('api-roadmaps-list-create'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['target_role'], "QA Automation Engineer")

    def test_api_toggle_milestone(self):
        self.api_client.force_authenticate(user=self.user)
        url = reverse('api-milestone-toggle', kwargs={'pk': self.milestone.id})
        resp = self.api_client.post(url, {'is_completed': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['is_completed'])
        self.assertEqual(resp.data['roadmap_progress_percentage'], 100)

    def test_api_curated_resources(self):
        LearningResource.objects.create(
            title="Django REST Framework Tutorial",
            category="Python",
            url="https://www.django-rest-framework.org"
        )
        self.api_client.force_authenticate(user=self.user)
        resp = self.api_client.get(reverse('api-learning-resources'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_api_report_content(self):
        self.api_client.force_authenticate(user=self.user)
        resp = self.api_client.post(reverse('api-report-content'), {
            'category': 'job_issue',
            'subject': 'Broken apply URL',
            'description': 'The apply URL for TechCorp job returns 404.'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['subject'], "Broken apply URL")
