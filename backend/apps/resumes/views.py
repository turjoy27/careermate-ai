import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from apps.ai_services.exceptions import AIServiceError
from .forms import (
    ResumeEducationForm,
    ResumeExperienceForm,
    ResumeForm,
    ResumeProjectForm,
)
from .models import Resume, ResumeEducation, ResumeExperience, ResumeProject
from .serializers import (
    ResumeEducationSerializer,
    ResumeExperienceSerializer,
    ResumeProjectSerializer,
    ResumeSerializer,
)
from .services import ResumeService


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ResumeListView(View):
    """Lists all CVs created by the user with preview and download options."""
    template_name = 'resumes/list.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        resumes = profile.resumes.all()
        return render(request, self.template_name, {
            'resumes': resumes,
            'profile': profile,
        })


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ResumeCreateView(View):
    """Initializes a new resume populated from current profile data."""
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        title = request.POST.get('title', 'My Professional Resume').strip() or 'My Professional Resume'
        resume = ResumeService.create_from_profile(profile, title=title)
        messages.success(request, f"Created new resume: '{resume.title}'. Start tailoring your sections below.")
        return redirect('resumes-builder', pk=resume.id)


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ResumeBuilderView(View):
    """Interactive split-view Resume Studio with live preview and AI enhancement triggers."""
    template_name = 'resumes/builder.html'

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(
            Resume.objects.prefetch_related('educations', 'experiences', 'projects'),
            pk=pk,
            profile=profile
        )

        form = ResumeForm(instance=resume)
        edu_form = ResumeEducationForm()
        exp_form = ResumeExperienceForm()
        proj_form = ResumeProjectForm()

        return render(request, self.template_name, {
            'resume': resume,
            'form': form,
            'edu_form': edu_form,
            'exp_form': exp_form,
            'proj_form': proj_form,
            'educations': resume.educations.all(),
            'experiences': resume.experiences.all(),
            'projects': resume.projects.all(),
        })

    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(Resume, pk=pk, profile=profile)
        form = ResumeForm(request.POST, instance=resume)

        if form.is_valid():
            form.save()
            messages.success(request, "Resume details updated successfully.")
            return redirect('resumes-builder', pk=resume.id)

        edu_form = ResumeEducationForm()
        exp_form = ResumeExperienceForm()
        proj_form = ResumeProjectForm()
        return render(request, self.template_name, {
            'resume': resume,
            'form': form,
            'edu_form': edu_form,
            'exp_form': exp_form,
            'proj_form': proj_form,
            'educations': resume.educations.all(),
            'experiences': resume.experiences.all(),
            'projects': resume.projects.all(),
        })


@login_required(login_url='accounts-login')
def add_resume_education(request, resume_id):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    if request.method == 'POST':
        form = ResumeEducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.resume = resume
            edu.save()
            messages.success(request, f"Education at {edu.institution} added.")
        else:
            messages.error(request, "Could not add education. Please check input values.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def delete_resume_education(request, resume_id, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    edu = get_object_or_404(ResumeEducation, pk=pk, resume=resume)
    edu.delete()
    messages.info(request, "Education entry removed from resume.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def add_resume_experience(request, resume_id):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    if request.method == 'POST':
        form = ResumeExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.resume = resume
            exp.save()
            messages.success(request, f"Experience at {exp.company} added.")
        else:
            messages.error(request, "Could not add experience. Please check input values.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def delete_resume_experience(request, resume_id, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    exp = get_object_or_404(ResumeExperience, pk=pk, resume=resume)
    exp.delete()
    messages.info(request, "Experience entry removed from resume.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def add_resume_project(request, resume_id):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    if request.method == 'POST':
        form = ResumeProjectForm(request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            proj.resume = resume
            proj.save()
            messages.success(request, f"Project '{proj.title}' added.")
        else:
            messages.error(request, "Could not add project. Please check input values.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def delete_resume_project(request, resume_id, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=resume_id, profile=profile)
    proj = get_object_or_404(ResumeProject, pk=pk, resume=resume)
    proj.delete()
    messages.info(request, "Project removed from resume.")
    return redirect('resumes-builder', pk=resume.id)


@login_required(login_url='accounts-login')
def delete_resume(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=pk, profile=profile)
    resume.delete()
    messages.info(request, "Resume deleted.")
    return redirect('resumes-list')


@login_required(login_url='accounts-login')
def export_pdf(request, pk):
    """Streams ATS-compliant ReportLab PDF download."""
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(
        Resume.objects.prefetch_related('educations', 'experiences', 'projects'),
        pk=pk,
        profile=profile
    )

    pdf_bytes = ResumeService.generate_pdf(resume)

    filename = f"{resume.full_name or 'CareerMate'}_Resume.pdf".replace(" ", "_")
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    disposition = 'attachment' if request.GET.get('download') == '1' else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response


# ==============================================================================
# AJAX AI Endpoints
# ==============================================================================

@login_required(login_url='accounts-login')
@require_POST
def ai_generate_summary(request, pk):
    """AJAX endpoint to generate professional summary via Gemini."""
    profile = get_object_or_404(UserProfile, user=request.user)
    resume = get_object_or_404(Resume, pk=pk, profile=profile)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        target_role = data.get('target_role') or resume.target_role
        summary = ResumeService.generate_ai_summary(resume, target_role=target_role)
        return JsonResponse({'status': 'success', 'summary': summary})
    except AIServiceError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=502)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='accounts-login')
@require_POST
def ai_enhance_bullet(request):
    """AJAX endpoint to polish a description or bullet point via Gemini."""
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        draft = data.get('draft_text', '').strip()
        context = data.get('context', '')
        if not draft:
            return JsonResponse({'status': 'error', 'message': 'Draft text is required.'}, status=400)

        result = ResumeService.enhance_bullet_point(draft, context=context)
        return JsonResponse({'status': 'success', **result})
    except AIServiceError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=502)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class ResumeListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        resumes = profile.resumes.all()
        serializer = ResumeSerializer(resumes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        title = request.data.get('title', 'My Professional Resume')
        resume = ResumeService.create_from_profile(profile, title=title)
        serializer = ResumeSerializer(resume)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResumeDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(Resume, pk=pk, profile=profile)
        serializer = ResumeSerializer(resume)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(Resume, pk=pk, profile=profile)
        serializer = ResumeSerializer(resume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(Resume, pk=pk, profile=profile)
        resume.delete()
        return Response({'message': 'Resume deleted.'}, status=status.HTTP_204_NO_CONTENT)


class ResumePDFExportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        resume = get_object_or_404(Resume, pk=pk, profile=profile)
        pdf_bytes = ResumeService.generate_pdf(resume)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.full_name}_Resume.pdf"'
        return response
