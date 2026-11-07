from django.urls import path
from .views import (
    ResumeBuilderView,
    ResumeCreateView,
    ResumeListView,
    add_resume_education,
    add_resume_experience,
    add_resume_project,
    ai_enhance_bullet,
    ai_generate_summary,
    delete_resume,
    delete_resume_education,
    delete_resume_experience,
    delete_resume_project,
    export_pdf,
)

urlpatterns = [
    path('', ResumeListView.as_view(), name='resumes-list'),
    path('create/', ResumeCreateView.as_view(), name='resumes-create'),
    path('<int:pk>/builder/', ResumeBuilderView.as_view(), name='resumes-builder'),
    path('<int:pk>/delete/', delete_resume, name='resumes-delete'),
    path('<int:pk>/export-pdf/', export_pdf, name='resumes-export-pdf'),

    # Section CRUD
    path('<int:resume_id>/education/add/', add_resume_education, name='resumes-add-education'),
    path('<int:resume_id>/education/<int:pk>/delete/', delete_resume_education, name='resumes-delete-education'),
    path('<int:resume_id>/experience/add/', add_resume_experience, name='resumes-add-experience'),
    path('<int:resume_id>/experience/<int:pk>/delete/', delete_resume_experience, name='resumes-delete-experience'),
    path('<int:resume_id>/project/add/', add_resume_project, name='resumes-add-project'),
    path('<int:resume_id>/project/<int:pk>/delete/', delete_resume_project, name='resumes-delete-project'),

    # AI Enhancements
    path('<int:pk>/ai-summary/', ai_generate_summary, name='resumes-ai-summary'),
    path('ai-enhance-bullet/', ai_enhance_bullet, name='resumes-ai-enhance-bullet'),
]
