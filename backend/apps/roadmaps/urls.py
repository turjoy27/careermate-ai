from django.urls import path
from .views import (
    ReportContentView,
    RoadmapCreateView,
    RoadmapDetailView,
    RoadmapListView,
    toggle_milestone_completion,
)

urlpatterns = [
    path('', RoadmapListView.as_view(), name='roadmaps-list'),
    path('create/', RoadmapCreateView.as_view(), name='roadmaps-create'),
    path('<int:pk>/', RoadmapDetailView.as_view(), name='roadmaps-detail'),
    path('milestones/<int:pk>/toggle/', toggle_milestone_completion, name='milestone-toggle'),
    path('report/', ReportContentView.as_view(), name='report-content'),
]
