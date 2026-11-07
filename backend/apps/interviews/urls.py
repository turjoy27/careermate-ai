from django.urls import path
from .views import (
    InterviewSessionView,
    InterviewSetupView,
    InterviewSummaryView,
    submit_interview_answer,
)

urlpatterns = [
    path('', InterviewSetupView.as_view(), name='interviews-setup'),
    path('<int:session_id>/', InterviewSessionView.as_view(), name='interviews-session'),
    path('<int:session_id>/questions/<int:question_id>/submit/', submit_interview_answer, name='interviews-submit-answer'),
    path('<int:session_id>/summary/', InterviewSummaryView.as_view(), name='interviews-summary'),
]
