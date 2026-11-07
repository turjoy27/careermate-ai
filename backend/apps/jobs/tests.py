from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, UserProfile, UserSkill
from apps.jobs.models import JobListing, SavedJob
from apps.jobs.matching import JobMatchEngine, normalize_skill


class JobListingModelTestCase(TestCase):
    def setUp(self):
        self.job = JobListing.objects.create(
            title="Django Backend Developer",
            company_name="TechCorp BD",
            location="Dhaka, Bangladesh",
            job_type="full_time",
            workplace_type="hybrid",
            experience_level="entry",
            required_skills_raw="Python, Django, MySQL, REST APIs",
            preferred_skills_raw="Docker, Redis, Celery",
            description="We are seeking an enthusiastic Django developer.",
            apply_url="https://example.com/jobs/1"
        )

    def test_skills_list_properties(self):
        self.assertEqual(
            self.job.required_skills_list,
            ["Python", "Django", "MySQL", "REST APIs"]
        )
        self.assertEqual(
            self.job.preferred_skills_list,
            ["Docker", "Redis", "Celery"]
        )

    def test_str_representation(self):
        self.assertEqual(str(self.job), "Django Backend Developer at TechCorp BD (Dhaka, Bangladesh)")


class JobMatchEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="StrongPassword123!",
            first_name="Rahim",
            last_name="Uddin"
        )
        self.profile = self.user.profile
        self.profile.target_career = "Python Backend Developer"
        self.profile.save()

        # Add user skills
        UserSkill.objects.create(profile=self.profile, skill_name="Python", proficiency="expert")
        UserSkill.objects.create(profile=self.profile, skill_name="Django", proficiency="intermediate")
        UserSkill.objects.create(profile=self.profile, skill_name="Docker", proficiency="beginner")

        self.job = JobListing.objects.create(
            title="Junior Backend Developer (Python)",
            company_name="Innovate Ltd",
            location="Dhaka",
            job_type="full_time",
            experience_level="entry",
            required_skills_raw="Python, Django, PostgreSQL, REST APIs",  # 4 required (user has 2 -> 50% * 80 = 40)
            preferred_skills_raw="Docker, Kubernetes",                     # 2 preferred (user has 1 -> 50% * 15 = 7.5)
            description="Great role."
        )

    def test_deterministic_scoring(self):
        fit = JobMatchEngine.evaluate_fit(self.profile, self.job)

        # Matched required: Python, Django (2/4) = 40.0 pts
        # Matched preferred: Docker (1/2) = 7.5 pts
        # Target role bonus: 'backend' or 'developer' matches title -> +5.0 pts
        # Total = 40 + 7.5 + 5.0 = 52.5 -> banker's rounded to 52%
        self.assertIn("match_score", fit)
        self.assertEqual(fit["match_score"], 52)
        self.assertIn("Python", fit["matched_required"])
        self.assertIn("Django", fit["matched_required"])
        self.assertIn("PostgreSQL", fit["missing_required"])
        self.assertIn("REST APIs", fit["missing_required"])
        self.assertIn("Docker", fit["matched_preferred"])
        self.assertIn("Kubernetes", fit["missing_preferred"])

    def test_skill_normalization_alias(self):
        self.assertEqual(normalize_skill("React.js"), "react")
        self.assertEqual(normalize_skill("NodeJS"), "node")
        self.assertEqual(normalize_skill("PostgreSQL"), "postgres")
        self.assertEqual(normalize_skill("RESTful API"), "rest apis")
        self.assertEqual(normalize_skill("k8s"), "kubernetes")

    def test_perfect_match_score(self):
        perfect_job = JobListing.objects.create(
            title="Python Developer",
            company_name="Perfect Fit",
            location="Remote",
            required_skills_raw="Python, Django",
            preferred_skills_raw="Docker",
            description="All skills match."
        )
        fit = JobMatchEngine.evaluate_fit(self.profile, perfect_job)
        # 80 (required) + 15 (preferred) + 5 (role bonus) = 100
        self.assertEqual(fit["match_score"], 100)
        self.assertEqual(len(fit["missing_required"]), 0)


class JobViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="jobseeker@example.com",
            password="StrongPassword123!",
            first_name="Job",
            last_name="Seeker"
        )
        self.profile = self.user.profile
        self.profile.target_career = "Django Engineer"
        self.profile.save()
        UserSkill.objects.create(profile=self.profile, skill_name="Django")

        self.job1 = JobListing.objects.create(
            title="Django Engineer",
            company_name="Acme Corp",
            location="Dhaka",
            job_type="full_time",
            experience_level="mid",
            required_skills_raw="Django, Python",
            description="Django role"
        )
        self.job2 = JobListing.objects.create(
            title="Frontend React Specialist",
            company_name="Design Hub",
            location="Remote",
            job_type="contract",
            experience_level="entry",
            required_skills_raw="React, Tailwind",
            description="Frontend role"
        )

    def test_job_list_view_authenticated(self):
        self.client.login(email="jobseeker@example.com", password="StrongPassword123!")
        response = self.client.get(reverse('jobs-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/list.html')
        self.assertContains(response, "Django Engineer")
        self.assertContains(response, "Frontend React Specialist")

    def test_job_list_filter_search(self):
        self.client.login(email="jobseeker@example.com", password="StrongPassword123!")
        response = self.client.get(reverse('jobs-list'), {'q': 'Frontend'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frontend React Specialist")
        self.assertNotContains(response, "Acme Corp")

    def test_job_detail_view(self):
        self.client.login(email="jobseeker@example.com", password="StrongPassword123!")
        response = self.client.get(reverse('jobs-detail', kwargs={'pk': self.job1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/detail.html')
        self.assertContains(response, "Acme Corp")
        self.assertIn('fit', response.context)
        self.assertEqual(response.context['fit']['match_score'], 45)

    def test_toggle_save_job(self):
        self.client.login(email="jobseeker@example.com", password="StrongPassword123!")
        toggle_url = reverse('jobs-toggle-save', kwargs={'pk': self.job1.id})

        # Save job
        resp = self.client.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['is_saved'])
        self.assertTrue(SavedJob.objects.filter(profile=self.profile, job=self.job1).exists())

        # Unsave job
        resp2 = self.client.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertFalse(data2['is_saved'])
        self.assertFalse(SavedJob.objects.filter(profile=self.profile, job=self.job1).exists())

    def test_saved_jobs_list_view(self):
        SavedJob.objects.create(profile=self.profile, job=self.job1)
        self.client.login(email="jobseeker@example.com", password="StrongPassword123!")
        response = self.client.get(reverse('jobs-saved'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Engineer")


class JobAPITestCase(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email="apitest@example.com",
            password="StrongPassword123!",
            first_name="API",
            last_name="Tester"
        )
        self.profile = self.user.profile
        self.job = JobListing.objects.create(
            title="Backend Architect",
            company_name="Cloud Scale",
            location="Chittagong",
            required_skills_raw="Go, Kubernetes",
            description="Cloud role"
        )

    def test_api_list_jobs_unauthorized(self):
        response = self.api_client.get(reverse('api-jobs-list'))
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_api_list_jobs_authorized(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(reverse('api-jobs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Backend Architect")

    def test_api_save_job_toggle(self):
        self.api_client.force_authenticate(user=self.user)
        url = reverse('api-jobs-save-toggle', kwargs={'pk': self.job.id})
        res = self.api_client.post(url)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_saved'])
