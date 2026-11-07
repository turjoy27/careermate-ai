from django.urls import path
from .views import (
    ResumeDetailAPIView,
    ResumeListCreateAPIView,
    ResumePDFExportAPIView,
    ai_enhance_bullet,
    ai_generate_summary,
)

urlpatterns = [
    path('', ResumeListCreateAPIView.as_view(), name='api-resumes-list-create'),
    path('<int:pk>/', ResumeDetailAPIView.as_view(), name='api-resumes-detail'),
    path('<int:pk>/export-pdf/', ResumePDFExportAPIView.as_view(), name='api-resumes-export-pdf'),
    path('<int:pk>/ai-summary/', ai_generate_summary, name='api-resumes-ai-summary'),
    path('ai-enhance-bullet/', ai_enhance_bullet, name='api-resumes-ai-enhance-bullet'),
]
