import json
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Education, Experience, UserProfile, UserSkill
from apps.ai_services.schemas import BulletPointEnhanceResponse, SummaryEnhanceResponse
from apps.resumes.models import Resume, ResumeEducation, ResumeExperience, ResumeProject
from apps.resumes.pdf_generator import ResumePDFGenerator
from apps.resumes.services import ResumeService

User = get_user_model()


class ResumeModelAndServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='resumetest@example.com',
            password='Password123!',
            first_name='Tariq',
            last_name='Anam'
        )
        self.profile = self.user.profile
        self.profile.headline = 'Senior Backend Architect'
        self.profile.city = 'Dhaka'
        self.profile.country = 'Bangladesh'
        self.profile.summary = 'Skilled software engineer with 3 years building web APIs.'
        self.profile.target_career = 'Principal Backend Engineer'
        self.profile.save()

        Education.objects.create(
            profile=self.profile,
            institution='BUET',
            degree='B.Sc.',
            field_of_study='CSE',
            start_date='2018-01-01',
            is_current=False,
            grade='3.90'
        )
        Experience.objects.create(
            profile=self.profile,
            company='InnoTech BD',
            position='Software Engineer',
            location='Dhaka',
            start_date='2022-01-01',
            is_current=True,
            description='Designed and deployed microservices.'
        )
        UserSkill.objects.create(profile=self.profile, skill_name='Python', category='technical')
        UserSkill.objects.create(profile=self.profile, skill_name='Django', category='technical')
        UserSkill.objects.create(profile=self.profile, skill_name='MySQL', category='tool')

    def test_create_resume_clones_profile_data(self):
        resume = ResumeService.create_from_profile(self.profile, title='Tariq Tech Resume')

        self.assertEqual(resume.full_name, 'Tariq Anam')
        self.assertEqual(resume.email, 'resumetest@example.com')
        self.assertIn('Dhaka', resume.location)
        self.assertIn('Python', resume.skills_list)
        self.assertIn('Django', resume.skills_list)

        # Cloned education
        self.assertEqual(resume.educations.count(), 1)
        edu = resume.educations.first()
        self.assertEqual(edu.institution, 'BUET')

        # Cloned experience
        self.assertEqual(resume.experiences.count(), 1)
        exp = resume.experiences.first()
        self.assertEqual(exp.company, 'InnoTech BD')

    def test_ai_summary_generation_service(self):
        resume = ResumeService.create_from_profile(self.profile)
        mock_ai = MagicMock()
        mock_ai.generate_professional_summary.return_value = SummaryEnhanceResponse(
            professional_summary='Tariq Anam is a dedicated Backend Architect based in Dhaka.',
            suggested_highlights=['Django', 'API Architecture']
        )

        summary = ResumeService.generate_ai_summary(resume, ai_service=mock_ai)
        self.assertIn('Tariq Anam is a dedicated Backend Architect', summary)

    def test_ai_bullet_enhancement_service(self):
        mock_ai = MagicMock()
        mock_ai.enhance_bullet_point.return_value = BulletPointEnhanceResponse(
            enhanced_text='Engineered and deployed scalable microservices using Django and MySQL.',
            improvements_made=['Used stronger action verb (Engineered)', 'Fixed grammar']
        )

        res = ResumeService.enhance_bullet_point('made microservices in django', ai_service=mock_ai)
        self.assertEqual(res['enhanced_text'], 'Engineered and deployed scalable microservices using Django and MySQL.')
        self.assertEqual(len(res['improvements_made']), 2)


class ReportLabPDFGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='pdftest@example.com',
            password='Password123!',
            first_name='Nafis',
            last_name='Iqbal'
        )
        self.resume = Resume.objects.create(
            profile=self.user.profile,
            title='PDF Generation Test',
            full_name='Nafis Iqbal',
            email='pdftest@example.com',
            phone='+8801700000000',
            location='Dhaka, Bangladesh',
            linkedin_url='https://linkedin.com/in/nafis',
            github_url='https://github.com/nafis',
            professional_summary='Results-driven Software Engineer with proven problem-solving abilities.',
            skills_raw='Python, Django, MySQL, PostgreSQL, Docker, Redis, REST APIs, Git'
        )
        ResumeEducation.objects.create(
            resume=self.resume,
            institution='University of Dhaka',
            degree='B.Sc.',
            field_of_study='Computer Science',
            start_date='2019',
            end_date='2023',
            grade='CGPA 3.82 / 4.00'
        )
        ResumeExperience.objects.create(
            resume=self.resume,
            company='Software Corp',
            position='Junior Developer',
            location='Dhaka',
            start_date='Jan 2023',
            end_date='Present',
            description='• Implemented authentication APIs.\n• Optimized database queries by 30%.'
        )
        ResumeProject.objects.create(
            resume=self.resume,
            title='CareerMate AI Platform',
            tech_stack='Python, Django, MySQL, Gemini SDK',
            github_link='https://github.com/careermate',
            description='• Built an AI career counseling platform tailored for Bangladesh graduates.'
        )

    def test_pdf_generation_returns_valid_pdf_bytes(self):
        generator = ResumePDFGenerator(self.resume)
        pdf_bytes = generator.generate()

        # PDF standard header
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        # Non-empty content
        self.assertGreater(len(pdf_bytes), 1000)

    def test_minimal_resume_pdf_generation(self):
        # Even with no optional sections, PDF generator must succeed without crashing
        minimal_resume = Resume.objects.create(
            profile=self.user.profile,
            title='Minimal Resume',
            full_name='Minimalist User',
            email='mini@example.com'
        )
        generator = ResumePDFGenerator(minimal_resume)
        pdf_bytes = generator.generate()
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))


class ResumeWebViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='webres@example.com',
            password='Password123!',
            first_name='Habib',
            last_name='Wahid'
        )
        self.profile = self.user.profile
        self.client.login(email='webres@example.com', password='Password123!')

    def test_resume_list_and_create_views(self):
        # List view empty
        res = self.client.get(reverse('resumes-list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'AI Resume Studio')

        # Create new resume POST
        create_res = self.client.post(reverse('resumes-create'), {'title': 'Full-Stack CV'}, follow=True)
        self.assertEqual(create_res.status_code, 200)

        resume = Resume.objects.get(profile=self.profile, title='Full-Stack CV')
        self.assertEqual(resume.full_name, 'Habib Wahid')

    def test_resume_builder_view_get_and_update(self):
        resume = ResumeService.create_from_profile(self.profile, title='My Studio Resume')

        # GET builder
        builder_url = reverse('resumes-builder', kwargs={'pk': resume.id})
        get_res = self.client.get(builder_url)
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'Live PDF Document Preview')

        # POST update
        post_data = {
            'title': 'Updated Title',
            'full_name': 'Habib Wahid, B.Sc.',
            'email': 'updated@example.com',
            'phone': '+8801811223344',
            'location': 'Chittagong, Bangladesh',
            'professional_summary': 'Updated professional summary statement.',
            'skills_raw': 'Python, Django, Celery',
            'template_style': 'modern_clean',
        }
        update_res = self.client.post(builder_url, post_data, follow=True)
        self.assertEqual(update_res.status_code, 200)

        resume.refresh_from_db()
        self.assertEqual(resume.full_name, 'Habib Wahid, B.Sc.')
        self.assertEqual(resume.location, 'Chittagong, Bangladesh')

    def test_export_pdf_http_response(self):
        resume = ResumeService.create_from_profile(self.profile, title='Downloadable Resume')
        url = reverse('resumes-export-pdf', kwargs={'pk': resume.id})

        response = self.client.get(url + '?download=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    @patch('apps.resumes.views.ResumeService.generate_ai_summary')
    def test_ajax_ai_summary_view(self, mock_gen_summary):
        mock_gen_summary.return_value = 'AI generated summary for testing.'
        resume = ResumeService.create_from_profile(self.profile)

        url = reverse('resumes-ai-summary', kwargs={'pk': resume.id})
        response = self.client.post(
            url,
            data=json.dumps({'target_role': 'Python Developer'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['summary'], 'AI generated summary for testing.')

    @patch('apps.resumes.views.ResumeService.enhance_bullet_point')
    def test_ajax_ai_enhance_bullet_view(self, mock_enhance):
        mock_enhance.return_value = {
            'enhanced_text': 'Polished description with action verb.',
            'improvements_made': ['Changed verb to active voice']
        }

        url = reverse('resumes-ai-enhance-bullet')
        response = self.client.post(
            url,
            data=json.dumps({'draft_text': 'handled database', 'context': 'work'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['enhanced_text'], 'Polished description with action verb.')


class ResumeAPITests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email='api_resume@example.com',
            password='Password123!',
            first_name='API',
            last_name='Tester'
        )
        self.profile = self.user.profile
        self.api_client.force_authenticate(user=self.user)

    def test_api_resume_crud_and_pdf(self):
        # Create
        create_res = self.api_client.post(
            reverse('api-resumes-list-create'),
            {'title': 'API Resume Test'},
            format='json'
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        resume_id = create_res.data['id']

        # Get Detail
        detail_res = self.api_client.get(reverse('api-resumes-detail', kwargs={'pk': resume_id}))
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['title'], 'API Resume Test')

        # Export PDF via API
        pdf_res = self.api_client.get(reverse('api-resumes-export-pdf', kwargs={'pk': resume_id}))
        self.assertEqual(pdf_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_res['Content-Type'], 'application/pdf')
        self.assertTrue(pdf_res.content.startswith(b'%PDF-'))
