from django.urls import path
from .views import (
    InterviewSessionDetailAPIView,
    InterviewSessionListCreateAPIView,
    InterviewSubmitAnswerAPIView,
)

urlpatterns = [
    path('', InterviewSessionListCreateAPIView.as_view(), name='api-interviews-list-create'),
    path('<int:session_id>/', InterviewSessionDetailAPIView.as_view(), name='api-interviews-detail'),
    path('<int:session_id>/questions/<int:question_id>/submit/', InterviewSubmitAnswerAPIView.as_view(), name='api-interviews-submit-answer'),
]

