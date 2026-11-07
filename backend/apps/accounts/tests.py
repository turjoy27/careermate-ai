import datetime
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Education, Experience, UserProfile, UserSkill

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_successful(self):
        email = 'student@example.com'
        password = 'SecurePassword123!'
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Rahim',
            last_name='Uddin',
            role='student'
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.full_name, 'Rahim Uddin')

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='password123')

    def test_create_superuser_successful(self):
        admin = User.objects.create_superuser(
            email='admin@careermate.ai',
            password='AdminPassword123!',
            first_name='System',
            last_name='Admin'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, 'admin')


class WebAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.reg_url = reverse('accounts-register')
        self.login_url = reverse('accounts-login')
        self.logout_url = reverse('accounts-logout')
        self.dashboard_url = reverse('dashboard-home')
        self.profile_url = reverse('accounts-profile')

    def test_user_registration_student_role(self):
        data = {
            'first_name': 'Arif',
            'last_name': 'Hasan',
            'email': 'arif@university.edu.bd',
            'role': 'student',
            'password': 'StrongPassword2026!',
            'password_confirm': 'StrongPassword2026!'
        }
        response = self.client.post(self.reg_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # User is created and auto-logged in
        user = User.objects.get(email='arif@university.edu.bd')
        self.assertEqual(user.role, 'student')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_user_registration_jobseeker_role(self):
        data = {
            'first_name': 'Nusrat',
            'last_name': 'Jahan',
            'email': 'nusrat@jobseeker.com',
            'role': 'jobseeker',
            'password': 'JobSeeker2026!',
            'password_confirm': 'JobSeeker2026!'
        }
        response = self.client.post(self.reg_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='nusrat@jobseeker.com')
        self.assertEqual(user.role, 'jobseeker')

    def test_user_registration_password_mismatch(self):
        data = {
            'first_name': 'Sadia',
            'last_name': 'Islam',
            'email': 'sadia@example.com',
            'role': 'student',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword456!'
        }
        response = self.client.post(self.reg_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='sadia@example.com').exists())

    def test_user_login_and_logout(self):
        user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        # Successful Login
        login_response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!'
        }, follow=True)
        self.assertEqual(login_response.status_code, 200)

        # Access protected dashboard
        dash_response = self.client.get(self.dashboard_url)
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, 'Test')

        # Logout
        logout_response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(logout_response.status_code, 200)

        # Accessing dashboard after logout redirects to login
        dash_after_logout = self.client.get(self.dashboard_url)
        self.assertEqual(dash_after_logout.status_code, 302)
        self.assertIn(self.login_url, dash_after_logout.url)

    def test_unauthorized_dashboard_access_redirects(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_unauthorized_profile_access_redirects(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)


class ProfileManagementWebTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='dev@careermate.ai',
            password='Password123!',
            first_name='Kamal',
            last_name='Ahmed',
            role='student'
        )
        self.profile = self.user.profile
        self.client.login(email='dev@careermate.ai', password='Password123!')

    def test_profile_update_post(self):
        data = {
            'headline': 'Full-Stack Developer in Training',
            'target_career': 'Full-Stack Python Engineer',
            'city': 'Dhaka',
            'country': 'Bangladesh',
            'phone': '+8801711223344',
            'summary': 'Dedicated to building scalable software.',
            'linkedin_url': 'https://linkedin.com/in/kamal',
            'github_url': 'https://github.com/kamal',
            'portfolio_url': 'https://kamal.dev',
        }
        response = self.client.post(reverse('accounts-profile'), data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.headline, 'Full-Stack Developer in Training')
        self.assertEqual(self.profile.target_career, 'Full-Stack Python Engineer')

    def test_add_and_delete_skill(self):
        # Add Skill
        add_url = reverse('accounts-add-skill')
        response = self.client.post(add_url, {
            'skill_name': 'Django',
            'category': 'technical',
            'proficiency': 'expert'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        skill = UserSkill.objects.get(profile=self.profile, skill_name='Django')
        self.assertEqual(skill.proficiency, 'expert')

        # Delete Skill
        del_url = reverse('accounts-delete-skill', kwargs={'pk': skill.id})
        del_response = self.client.get(del_url, follow=True)
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(UserSkill.objects.filter(pk=skill.id).exists())

    def test_add_and_delete_education(self):
        # Add Education
        add_url = reverse('accounts-add-education')
        data = {
            'institution': 'BRAC University',
            'degree': 'B.Sc.',
            'field_of_study': 'Computer Science',
            'start_date': '2021-01-01',
            'end_date': '2025-01-01',
            'is_current': False,
            'grade': '3.90'
        }
        response = self.client.post(add_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        edu = Education.objects.get(profile=self.profile, institution='BRAC University')
        self.assertEqual(edu.degree, 'B.Sc.')

        # Delete Education
        del_url = reverse('accounts-delete-education', kwargs={'pk': edu.id})
        del_response = self.client.get(del_url, follow=True)
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(Education.objects.filter(pk=edu.id).exists())


class RestAPIAccountsTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email='apiuser@example.com',
            password='ApiPassword123!',
            first_name='API',
            last_name='User'
        )

    def test_api_register_success(self):
        data = {
            'email': 'newapi@example.com',
            'first_name': 'New',
            'last_name': 'API',
            'role': 'jobseeker',
            'password': 'StrongPassword2026!',
            'password_confirm': 'StrongPassword2026!'
        }
        response = self.api_client.post(reverse('api-accounts-register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'newapi@example.com')

    def test_api_login_success(self):
        data = {
            'email': 'apiuser@example.com',
            'password': 'ApiPassword123!'
        }
        response = self.api_client.post(reverse('api-accounts-login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_unauthenticated_api_profile_fails(self):
        response = self.api_client.get(reverse('api-accounts-profile'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_api_profile_and_skills(self):
        self.api_client.force_authenticate(user=self.user)

        # GET Profile
        response = self.api_client.get(reverse('api-accounts-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # PUT Profile update
        update_data = {
            'headline': 'API Architect',
            'target_career': 'Senior Cloud Engineer'
        }
        put_response = self.api_client.put(reverse('api-accounts-profile'), update_data, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.assertEqual(put_response.data['headline'], 'API Architect')

        # Add Skill via API
        skill_data = {
            'skill_name': 'Kubernetes',
            'category': 'tool',
            'proficiency': 'intermediate'
        }
        skill_res = self.api_client.post(reverse('api-accounts-skills'), skill_data, format='json')
        self.assertEqual(skill_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(skill_res.data['skill_name'], 'Kubernetes')
