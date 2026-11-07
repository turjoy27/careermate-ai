from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.models import User, UserProfile
from apps.interviews.models import InterviewSession
from apps.jobs.models import JobListing, SavedJob
from apps.resumes.models import Resume
from apps.roadmaps.models import LearningResource, LearningRoadmap, ReportedContent


class LandingView(View):
    """Public landing page showcasing CareerMate AI features."""
    template_name = 'dashboard/landing.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard-home')
        return render(request, self.template_name)


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class DashboardHomeView(View):
    """Protected main dashboard providing personalized career overview and analytics."""
    template_name = 'dashboard/index.html'

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Calculate dynamic profile completion percentage
        completion = 0
        checks = []

        if user.first_name and user.last_name:
            completion += 15
            checks.append({'label': 'Basic Info', 'done': True})
        else:
            checks.append({'label': 'Basic Info', 'done': False})

        if profile.headline:
            completion += 15
            checks.append({'label': 'Professional Headline', 'done': True})
        else:
            checks.append({'label': 'Professional Headline', 'done': False})

        if profile.target_career:
            completion += 20
            checks.append({'label': 'Target Career Goal', 'done': True})
        else:
            checks.append({'label': 'Target Career Goal', 'done': False})

        if profile.summary:
            completion += 15
            checks.append({'label': 'Career Summary', 'done': True})
        else:
            checks.append({'label': 'Career Summary', 'done': False})

        skills_count = profile.skills.count()
        if skills_count >= 3:
            completion += 20
            checks.append({'label': 'Skills (3+ added)', 'done': True})
        elif skills_count > 0:
            completion += 10
            checks.append({'label': f'Skills ({skills_count}/3 added)', 'done': False})
        else:
            checks.append({'label': 'Skills (None added)', 'done': False})

        educations_count = profile.educations.count()
        if educations_count >= 1:
            completion += 15
            checks.append({'label': 'Education Record', 'done': True})
        else:
            checks.append({'label': 'Education Record', 'done': False})

        completion = min(completion, 100)

        context = {
            'user': user,
            'profile': profile,
            'completion': completion,
            'completion_checks': checks,
            'skills_count': skills_count,
            'educations_count': educations_count,
            'experiences_count': profile.experiences.count(),
            'skills': profile.skills.all()[:8],
            'educations': profile.educations.all()[:3],
        }
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class AdminAnalyticsDashboardView(View):
    """Platform Administration Dashboard presenting system-wide analytics, metrics, and moderation."""
    template_name = 'dashboard/admin_analytics.html'

    def get(self, request):
        if not (request.user.is_staff or request.user.role == 'admin'):
            raise PermissionDenied("Administrative credentials required to view platform analytics.")

        # User statistics
        total_users = User.objects.count()
        student_count = User.objects.filter(role='student').count()
        jobseeker_count = User.objects.filter(role='jobseeker').count()
        admin_count = User.objects.filter(role='admin').count()

        # Resumes & Careers
        total_resumes = Resume.objects.count()

        # Interviews
        total_interviews = InterviewSession.objects.count()
        completed_interviews = InterviewSession.objects.filter(is_completed=True).count()
        avg_interview_score = InterviewSession.objects.filter(overall_score__isnull=False).aggregate(
            avg=Avg('overall_score')
        )['avg']
        avg_interview_score = round(avg_interview_score, 1) if avg_interview_score else 0.0

        # Learning Roadmaps
        total_roadmaps = LearningRoadmap.objects.count()
        avg_roadmap_progress = LearningRoadmap.objects.aggregate(avg=Avg('progress_percentage'))['avg']
        avg_roadmap_progress = round(avg_roadmap_progress, 1) if avg_roadmap_progress else 0.0

        # Job Market
        total_jobs = JobListing.objects.count()
        active_jobs = JobListing.objects.filter(is_active=True).count()
        total_saved_jobs = SavedJob.objects.count()

        # Moderation & Feedback
        pending_reports = ReportedContent.objects.filter(status='pending').count()
        recent_reports = ReportedContent.objects.select_related('user').order_by('-created_at')[:8]
        recent_users = User.objects.order_by('-date_joined')[:8]
        curated_resources_count = LearningResource.objects.count()

        context = {
            'total_users': total_users,
            'student_count': student_count,
            'jobseeker_count': jobseeker_count,
            'admin_count': admin_count,
            'total_resumes': total_resumes,
            'total_interviews': total_interviews,
            'completed_interviews': completed_interviews,
            'avg_interview_score': avg_interview_score,
            'total_roadmaps': total_roadmaps,
            'avg_roadmap_progress': avg_roadmap_progress,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_saved_jobs': total_saved_jobs,
            'pending_reports': pending_reports,
            'recent_reports': recent_reports,
            'recent_users': recent_users,
            'curated_resources_count': curated_resources_count,
        }
        return render(request, self.template_name, context)

