from django.urls import path
from .views import (
    JobDetailView,
    JobListView,
    SavedJobsListView,
    toggle_save_job,
)

urlpatterns = [
    path('', JobListView.as_view(), name='jobs-list'),
    path('saved/', SavedJobsListView.as_view(), name='jobs-saved'),
    path('<int:pk>/', JobDetailView.as_view(), name='jobs-detail'),
    path('<int:pk>/save/', toggle_save_job, name='jobs-toggle-save'),
]
