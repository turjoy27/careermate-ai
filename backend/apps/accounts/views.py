from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView,
)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    EducationForm,
    UserLoginForm,
    UserProfileForm,
    UserRegistrationForm,
    UserSkillForm,
)
from .models import Education, UserProfile, UserSkill
from .serializers import (
    EducationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSkillSerializer,
)


# ==============================================================================
# Web UI Views (Session-based)
# ==============================================================================

class RegisterView(View):
    """User registration view supporting Student and Job Seeker accounts."""
    template_name = 'auth/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard-home')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to CareerMate AI, {user.first_name}! Let's set up your career profile."
            )
            return redirect('accounts-onboarding')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """Email-based login view."""
    template_name = 'auth/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard-home')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Browser close expiration
            messages.success(request, f"Welcome back, {user.first_name or user.email}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard-home')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Secure logout view with POST/GET support."""
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('accounts-login')

    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('accounts-login')


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class OnboardingView(View):
    """Initial onboarding wizard for new students and job seekers."""
    template_name = 'accounts/onboarding.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(instance=profile)
        edu_form = EducationForm()
        skill_form = UserSkillForm()
        return render(request, self.template_name, {
            'profile': profile,
            'profile_form': profile_form,
            'edu_form': edu_form,
            'skill_form': skill_form,
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Onboarding complete! Your career workspace is ready.")
            return redirect('dashboard-home')

        edu_form = EducationForm()
        skill_form = UserSkillForm()
        return render(request, self.template_name, {
            'profile': profile,
            'profile_form': profile_form,
            'edu_form': edu_form,
            'skill_form': skill_form,
        })


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ProfileView(View):
    """Comprehensive profile editing page with Education and Skills management."""
    template_name = 'accounts/profile.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(instance=profile)
        edu_form = EducationForm()
        skill_form = UserSkillForm()
        return render(request, self.template_name, {
            'profile': profile,
            'profile_form': profile_form,
            'edu_form': edu_form,
            'skill_form': skill_form,
            'educations': profile.educations.all(),
            'skills': profile.skills.all(),
            'experiences': profile.experiences.all(),
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('accounts-profile')

        edu_form = EducationForm()
        skill_form = UserSkillForm()
        return render(request, self.template_name, {
            'profile': profile,
            'profile_form': profile_form,
            'edu_form': edu_form,
            'skill_form': skill_form,
            'educations': profile.educations.all(),
            'skills': profile.skills.all(),
            'experiences': profile.experiences.all(),
        })


@login_required(login_url='accounts-login')
def add_education(request):
    """Handle education addition via form submit."""
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.profile = profile
            education.save()
            messages.success(request, f"Education at {education.institution} added.")
        else:
            messages.error(request, "Could not add education. Please check input values.")
    return redirect('accounts-profile')


@login_required(login_url='accounts-login')
def delete_education(request, pk):
    """Delete an education item belonging to the current user."""
    profile = get_object_or_404(UserProfile, user=request.user)
    education = get_object_or_404(Education, pk=pk, profile=profile)
    education.delete()
    messages.info(request, "Education entry removed.")
    return redirect('accounts-profile')


@login_required(login_url='accounts-login')
def add_skill(request):
    """Handle skill addition via form submit."""
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = UserSkillForm(request.POST)
        if form.is_valid():
            skill_name = form.cleaned_data['skill_name'].strip()
            category = form.cleaned_data['category']
            proficiency = form.cleaned_data['proficiency']
            skill, created = UserSkill.objects.update_or_create(
                profile=profile,
                skill_name=skill_name,
                defaults={'category': category, 'proficiency': proficiency}
            )
            msg = f"Skill '{skill_name}' added." if created else f"Skill '{skill_name}' updated."
            messages.success(request, msg)
        else:
            messages.error(request, "Failed to add skill. Please check your input.")
    return redirect('accounts-profile')


@login_required(login_url='accounts-login')
def delete_skill(request, pk):
    """Delete a skill belonging to the current user."""
    profile = get_object_or_404(UserProfile, user=request.user)
    skill = get_object_or_404(UserSkill, pk=pk, profile=profile)
    skill.delete()
    messages.info(request, f"Skill '{skill.skill_name}' removed.")
    return redirect('accounts-profile')


# ==============================================================================
# Password Reset Workflow (Django standard views customized)
# ==============================================================================

class PasswordResetView(BasePasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('accounts-password-reset-done')


class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('accounts-password-reset-complete')


class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class RegisterAPIView(APIView):
    """API endpoint to register new user accounts."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """API endpoint for authenticating and establishing session."""
    permission_classes = [AllowAny]

    def post(self, request):
        form = UserLoginForm(request.data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return Response({
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name,
                }
            }, status=status.HTTP_200_OK)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """API endpoint to destroy current session."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    """API endpoint to retrieve and update user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SkillListCreateAPIView(APIView):
    """API endpoint to list and add user skills."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        skills = profile.skills.all()
        serializer = UserSkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserSkillSerializer(data=request.data)
        if serializer.is_valid():
            skill_name = serializer.validated_data['skill_name'].strip()
            category = serializer.validated_data.get('category', 'technical')
            proficiency = serializer.validated_data.get('proficiency', 'intermediate')
            skill, created = UserSkill.objects.update_or_create(
                profile=profile,
                skill_name=skill_name,
                defaults={'category': category, 'proficiency': proficiency}
            )
            return Response(UserSkillSerializer(skill).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SkillDetailAPIView(APIView):
    """API endpoint to delete a skill."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        skill = get_object_or_404(UserSkill, pk=pk, profile=profile)
        skill.delete()
        return Response({'message': 'Skill deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class EducationListCreateAPIView(APIView):
    """API endpoint to list and create educations."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        educations = profile.educations.all()
        serializer = EducationSerializer(educations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            education = serializer.save(profile=profile)
            return Response(EducationSerializer(education).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EducationDetailAPIView(APIView):
    """API endpoint to delete an education."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        education = get_object_or_404(Education, pk=pk, profile=profile)
        education.delete()
        return Response({'message': 'Education deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
