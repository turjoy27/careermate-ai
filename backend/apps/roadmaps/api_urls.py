from django.urls import path
from .views import (
    LearningResourceListAPIView,
    ReportContentCreateAPIView,
    RoadmapDetailAPIView,
    RoadmapListCreateAPIView,
    RoadmapMilestoneToggleAPIView,
)

urlpatterns = [
    path('', RoadmapListCreateAPIView.as_view(), name='api-roadmaps-list-create'),
    path('<int:pk>/', RoadmapDetailAPIView.as_view(), name='api-roadmaps-detail'),
    path('milestones/<int:pk>/toggle/', RoadmapMilestoneToggleAPIView.as_view(), name='api-milestone-toggle'),
    path('resources/', LearningResourceListAPIView.as_view(), name='api-learning-resources'),
    path('report/', ReportContentCreateAPIView.as_view(), name='api-report-content'),
]
