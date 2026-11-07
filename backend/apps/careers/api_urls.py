from django.urls import path
from .views import (
    CareerDetailAPIView,
    CareerHistoryAPIView,
    CareerRecommendAPIView,
    SkillGapAPIView,
)

urlpatterns = [
    path('recommend/', CareerRecommendAPIView.as_view(), name='api-careers-recommend'),
    path('history/', CareerHistoryAPIView.as_view(), name='api-careers-history'),
    path('<int:pk>/', CareerDetailAPIView.as_view(), name='api-careers-detail'),
    path('<int:pk>/skill-gap/', SkillGapAPIView.as_view(), name='api-careers-skill-gap'),
]
