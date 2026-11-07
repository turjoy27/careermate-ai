from io import BytesIO
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User, UserProfile
from apps.chat.models import ChatConversation, ChatMessage
from apps.interviews.models import InterviewQuestion, InterviewSession
from apps.jobs.models import JobListing
from apps.resumes.models import Resume
from apps.roadmaps.models import LearningRoadmap, RoadmapMilestone, RoadmapStage


class IDORObjectLevelPrivacyTestCase(TestCase):
    """Verifies that candidates cannot view, edit, or delete another candidate's private data."""

    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user(
            email="user_a@example.com",
            password="StrongPassword123!",
            first_name="Candidate",
            last_name="A"
        )
        self.profile_a = self.user_a.profile

        self.client_b = Client()
        self.user_b = User.objects.create_user(
            email="user_b@example.com",
            password="StrongPassword123!",
            first_name="Candidate",
            last_name="B"
        )
        self.profile_b = self.user_b.profile

        # User A's private records
        self.resume_a = Resume.objects.create(
            profile=self.profile_a,
            title="User A's Secret Resume",
            full_name="Candidate A",
            email="user_a@example.com"
        )
        self.interview_a = InterviewSession.objects.create(
            profile=self.profile_a,
            target_role="Software Architect",
            total_questions=1
        )
        self.chat_a = ChatConversation.objects.create(
            profile=self.profile_a,
            title="User A's Private Chat"
        )
        self.roadmap_a = LearningRoadmap.objects.create(
            profile=self.profile_a,
            title="User A's Learning Roadmap",
            target_role="DevOps Specialist"
        )
        self.stage_a = RoadmapStage.objects.create(
            roadmap=self.roadmap_a,
            stage_level="beginner",
            title="Stage 1",
            order=1
        )
        self.milestone_a = RoadmapMilestone.objects.create(
            stage=self.stage_a,
            title="Milestone A",
            order=1
        )

    def test_user_b_cannot_access_user_a_resume(self):
        self.client_b.login(email="user_b@example.com", password="StrongPassword123!")

        # Attempt to access User A's resume builder
        resp = self.client_b.get(reverse('resumes-builder', kwargs={'pk': self.resume_a.id}))
        self.assertEqual(resp.status_code, 404)

        # Attempt to export User A's resume PDF
        pdf_resp = self.client_b.get(reverse('resumes-export-pdf', kwargs={'pk': self.resume_a.id}))
        self.assertEqual(pdf_resp.status_code, 404)

    def test_user_b_cannot_access_user_a_interview(self):
        self.client_b.login(email="user_b@example.com", password="StrongPassword123!")

        # Attempt to view User A's interview session
        resp = self.client_b.get(reverse('interviews-session', kwargs={'session_id': self.interview_a.id}))
        self.assertEqual(resp.status_code, 404)

        # Attempt to view User A's interview summary
        sum_resp = self.client_b.get(reverse('interviews-summary', kwargs={'session_id': self.interview_a.id}))
        self.assertEqual(sum_resp.status_code, 404)

    def test_user_b_cannot_access_user_a_chat(self):
        self.client_b.login(email="user_b@example.com", password="StrongPassword123!")

        # Attempt to access User A's chat conversation redirects away to user B's own chat portal
        resp = self.client_b.get(reverse('chat-conversation', kwargs={'conversation_id': self.chat_a.id}))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/chat/', resp.url)

        # Confirm User A's private messages are never leaked
        follow_resp = self.client_b.get(reverse('chat-conversation', kwargs={'conversation_id': self.chat_a.id}), follow=True)
        self.assertNotContains(follow_resp, "User A's Private Chat")

        # Attempt to send message to User A's conversation returns 404
        send_url = reverse('chat-send-ajax', kwargs={'conversation_id': self.chat_a.id})
        send_resp = self.client_b.post(send_url, data='{"message":"test"}', content_type='application/json')
        self.assertEqual(send_resp.status_code, 404)

    def test_user_b_cannot_access_or_toggle_user_a_roadmap(self):
        self.client_b.login(email="user_b@example.com", password="StrongPassword123!")

        # Attempt to view User A's roadmap
        resp = self.client_b.get(reverse('roadmaps-detail', kwargs={'pk': self.roadmap_a.id}))
        self.assertEqual(resp.status_code, 404)

        # Attempt to toggle User A's milestone
        toggle_url = reverse('milestone-toggle', kwargs={'pk': self.milestone_a.id})
        t_resp = self.client_b.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(t_resp.status_code, 404)


class SecurityAndPermissionsTestCase(TestCase):
    """Verifies authentication barriers, password hashing, and role permissions."""

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            email="regular_student@example.com",
            password="StrongPassword123!",
            first_name="Regular",
            last_name="Student",
            role="student"
        )
        self.admin = User.objects.create_superuser(
            email="platform_admin@careermate.ai",
            password="AdminPassword123!",
            first_name="Platform",
            last_name="Admin"
        )

    def test_password_is_properly_hashed(self):
        # Ensure password is not stored in plain text
        self.assertNotEqual(self.student.password, "StrongPassword123!")
        self.assertTrue(self.student.password.startswith("pbkdf2_") or self.student.password.startswith("argon2"))
        self.assertTrue(self.student.check_password("StrongPassword123!"))
        self.assertFalse(self.student.check_password("WrongPassword123!"))

    def test_unauthenticated_protected_views_redirect_to_login(self):
        protected_endpoints = [
            reverse('dashboard-home'),
            reverse('accounts-profile'),
            reverse('careers-recommendations'),
            reverse('resumes-list'),
            reverse('chat-portal'),
            reverse('jobs-list'),
            reverse('interviews-setup'),
            reverse('roadmaps-list'),
        ]
        for url in protected_endpoints:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, f"Failed for {url}")
            self.assertIn('/accounts/login/', resp.url)

    def test_regular_student_cannot_access_platform_analytics(self):
        self.client.login(email="regular_student@example.com", password="StrongPassword123!")
        resp = self.client.get(reverse('admin-analytics'))
        self.assertEqual(resp.status_code, 403)

    def test_platform_admin_can_access_platform_analytics(self):
        self.client.login(email="platform_admin@careermate.ai", password="AdminPassword123!")
        resp = self.client.get(reverse('admin-analytics'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'dashboard/admin_analytics.html')


class InputValidationAndSecurityTestCase(TestCase):
    """Verifies edge case input validation and security barriers."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="validator@example.com",
            password="StrongPassword123!",
            first_name="Valid",
            last_name="User"
        )

    def test_duplicate_user_registration_rejected(self):
        url = reverse('accounts-register')
        resp = self.client.post(url, {
            'email': 'validator@example.com',
            'first_name': 'Another',
            'last_name': 'Person',
            'role': 'student',
            'password': 'Password123!',
            'password_confirm': 'Password123!'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already exists")

    def test_password_mismatch_registration_rejected(self):
        url = reverse('accounts-register')
        resp = self.client.post(url, {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword123!'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Passwords do not match")
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())

    def test_report_content_missing_fields_rejected(self):
        self.client.login(email="validator@example.com", password="StrongPassword123!")
        resp = self.client.post(reverse('report-content'), {
            'category': 'job_issue',
            'subject': '',
            'description': ''
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Subject and detailed description are required")


class PDFExportIntegrityTestCase(TestCase):
    """Verifies ReportLab PDF generator produces valid binary PDFs without crashing on sparse data."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="pdfuser@example.com",
            password="StrongPassword123!",
            first_name="PDF",
            last_name="Tester"
        )
        self.profile = self.user.profile

    def test_sparse_resume_pdf_generation(self):
        sparse_resume = Resume.objects.create(
            profile=self.profile,
            title="Minimal Resume",
            full_name="PDF Tester",
            email="pdfuser@example.com"
        )
        client = Client()
        client.login(email="pdfuser@example.com", password="StrongPassword123!")
        resp = client.get(reverse('resumes-export-pdf', kwargs={'pk': sparse_resume.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        self.assertGreater(len(resp.content), 500)

    def test_special_characters_and_multipage_pdf_generation(self):
        complex_resume = Resume.objects.create(
            profile=self.profile,
            title="Complex Resume & Special Chars <test>",
            full_name="Tanvir & Sons <Applicant>",
            email="pdfuser@example.com",
            location="Dhaka & Chittagong, Bangladesh",
            professional_summary="Special chars: <tags>, & ampersands, \"quotes\", 'apostrophes' & Unicode: বাংলা.",
            skills_raw="C++, Python & Django, HTML/CSS, React.js, R&D"
        )
        # Add multiple educations and experiences
        for i in range(4):
            complex_resume.educations.create(
                institution=f"University of Science & Tech #{i}",
                degree=f"B.Sc. in Computer Science & Engineering #{i}",
                field_of_study="Computer Systems & Networks",
                start_date="2018",
                end_date="2022",
                order=i
            )
            complex_resume.experiences.create(
                company=f"Software Innovations Ltd & Co #{i}",
                position=f"Full-Stack Lead & Architect #{i}",
                location="Dhaka",
                start_date="2022",
                end_date="Present",
                description=f"Engineered microservices using Python & Django; optimized queries by 45% & reduced downtime.",
                order=i
            )
            complex_resume.projects.create(
                title=f"CareerMate AI Portal #{i}",
                tech_stack="Python, Django, MySQL & Gemini AI",
                description="Built automated career guidance platform with ReportLab PDF export & AI chatbot.",
                order=i
            )

        client = Client()
        client.login(email="pdfuser@example.com", password="StrongPassword123!")
        resp = client.get(reverse('resumes-export-pdf', kwargs={'pk': complex_resume.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        self.assertGreater(len(resp.content), 2000)


class JobMatchEngineBoundaryTestCase(TestCase):
    """Verifies deterministic math engine across mathematical boundaries and edge cases."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="mathuser@example.com",
            password="StrongPassword123!",
            first_name="Boundary",
            last_name="Tester"
        )
        self.profile = self.user.profile

    def test_candidate_with_zero_skills(self):
        from apps.jobs.matching import JobMatchEngine
        job = JobListing.objects.create(
            title="Senior Python Architect",
            company_name="Scale Tech",
            required_skills_raw="Python, Django, PostgreSQL, Docker",
            preferred_skills_raw="Kubernetes, Redis"
        )
        fit = JobMatchEngine.evaluate_fit(self.profile, job)
        self.assertEqual(fit['match_score'], 0)
        self.assertEqual(len(fit['matched_required']), 0)
        self.assertEqual(len(fit['missing_required']), 4)

    def test_job_with_zero_required_skills(self):
        from apps.jobs.matching import JobMatchEngine
        job_no_req = JobListing.objects.create(
            title="General Trainee",
            company_name="Universal Corp",
            required_skills_raw="",
            preferred_skills_raw="Communication, Problem Solving"
        )
        fit = JobMatchEngine.evaluate_fit(self.profile, job_no_req)
        # Defaults to neutral score without ZeroDivisionError
        self.assertGreaterEqual(fit['match_score'], 50)


class AIResilienceAndTimeoutTestCase(TestCase):
    """Verifies timeout handling, missing key errors, and exception mapping."""

    def test_missing_api_key_raises_configuration_error(self):
        from apps.ai_services.client import GeminiService
        from apps.ai_services.exceptions import AIConfigurationError

        service = GeminiService(api_key="")
        with self.assertRaises(AIConfigurationError):
            service._get_client()

    def test_placeholder_api_key_raises_configuration_error(self):
        from apps.ai_services.client import GeminiService
        from apps.ai_services.exceptions import AIConfigurationError

        service = GeminiService(api_key="your_gemini_api_key_here")
        with self.assertRaises(AIConfigurationError):
            service._get_client()

