from django.urls import path
from .views import (
    JobDetailAPIView,
    JobListAPIView,
    JobSaveToggleAPIView,
    SavedJobsListAPIView,
)

urlpatterns = [
    path('', JobListAPIView.as_view(), name='api-jobs-list'),
    path('saved/', SavedJobsListAPIView.as_view(), name='api-jobs-saved'),
    path('<int:pk>/', JobDetailAPIView.as_view(), name='api-jobs-detail'),
    path('<int:pk>/save/', JobSaveToggleAPIView.as_view(), name='api-jobs-save-toggle'),
]
