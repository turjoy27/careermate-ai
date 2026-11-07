"""
Master URL configuration for careermate_core project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import HealthCheckView

urlpatterns = [
    # Django Administration
    path('admin/', admin.site.urls),

    # Health Check API
    path('api/health/', HealthCheckView.as_view(), name='api-health-check'),

    # Accounts & Authentication (Web UI)
    path('accounts/', include('apps.accounts.urls')),

    # Accounts & Authentication (REST APIs)
    path('api/accounts/', include('apps.accounts.api_urls')),

    # Careers & Recommendations (Web UI)
    path('careers/', include('apps.careers.urls')),

    # Careers & Recommendations (REST APIs)
    path('api/careers/', include('apps.careers.api_urls')),

    # Resumes & CV Builder (Web UI)
    path('resumes/', include('apps.resumes.urls')),

    # Resumes & CV Builder (REST APIs)
    path('api/resumes/', include('apps.resumes.api_urls')),

    # AI Career Chatbot (Web UI)
    path('chat/', include('apps.chat.urls')),

    # AI Career Chatbot (REST APIs)
    path('api/chat/', include('apps.chat.api_urls')),

    # Job Matching (Web UI)
    path('jobs/', include('apps.jobs.urls')),

    # Job Matching (REST APIs)
    path('api/jobs/', include('apps.jobs.api_urls')),

    # Mock Interview Arena (Web UI)
    path('interviews/', include('apps.interviews.urls')),

    # Mock Interview Arena (REST APIs)
    path('api/interviews/', include('apps.interviews.api_urls')),

    # Learning Roadmaps (Web UI)
    path('roadmaps/', include('apps.roadmaps.urls')),

    # Learning Roadmaps (REST APIs)
    path('api/roadmaps/', include('apps.roadmaps.api_urls')),

    # Dashboard & Landing
    path('', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
