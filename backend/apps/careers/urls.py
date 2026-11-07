from django.urls import path
from .views import (
    CareerDetailView,
    CareerHistoryView,
    CareerRecommendationsView,
)

urlpatterns = [
    path('', CareerRecommendationsView.as_view(), name='careers-recommendations'),
    path('<int:pk>/', CareerDetailView.as_view(), name='careers-detail'),
    path('history/', CareerHistoryView.as_view(), name='careers-history'),
]
