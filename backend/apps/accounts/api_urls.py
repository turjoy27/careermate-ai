from django.urls import path
from .views import (
    EducationDetailAPIView,
    EducationListCreateAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileAPIView,
    RegisterAPIView,
    SkillDetailAPIView,
    SkillListCreateAPIView,
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api-accounts-register'),
    path('login/', LoginAPIView.as_view(), name='api-accounts-login'),
    path('logout/', LogoutAPIView.as_view(), name='api-accounts-logout'),
    path('profile/', ProfileAPIView.as_view(), name='api-accounts-profile'),
    path('skills/', SkillListCreateAPIView.as_view(), name='api-accounts-skills'),
    path('skills/<int:pk>/', SkillDetailAPIView.as_view(), name='api-accounts-skill-detail'),
    path('educations/', EducationListCreateAPIView.as_view(), name='api-accounts-educations'),
    path('educations/<int:pk>/', EducationDetailAPIView.as_view(), name='api-accounts-education-detail'),
]
