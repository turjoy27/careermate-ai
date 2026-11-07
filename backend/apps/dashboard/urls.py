from django.urls import path
from .views import AdminAnalyticsDashboardView, DashboardHomeView, LandingView

urlpatterns = [
    path('', LandingView.as_view(), name='landing-home'),
    path('dashboard/', DashboardHomeView.as_view(), name='dashboard-home'),
    path('admin-analytics/', AdminAnalyticsDashboardView.as_view(), name='admin-analytics'),
]
