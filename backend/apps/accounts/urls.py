from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    OnboardingView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    ProfileView,
    RegisterView,
    add_education,
    add_skill,
    delete_education,
    delete_skill,
)

urlpatterns = [
    # Web UI Authentication
    path('register/', RegisterView.as_view(), name='accounts-register'),
    path('login/', LoginView.as_view(), name='accounts-login'),
    path('logout/', LogoutView.as_view(), name='accounts-logout'),

    # Profile & Onboarding
    path('onboarding/', OnboardingView.as_view(), name='accounts-onboarding'),
    path('profile/', ProfileView.as_view(), name='accounts-profile'),
    path('education/add/', add_education, name='accounts-add-education'),
    path('education/<int:pk>/delete/', delete_education, name='accounts-delete-education'),
    path('skills/add/', add_skill, name='accounts-add-skill'),
    path('skills/<int:pk>/delete/', delete_skill, name='accounts-delete-skill'),

    # Password Reset Flow
    path('password-reset/', PasswordResetView.as_view(), name='accounts-password-reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='accounts-password-reset-done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='accounts-password-reset-complete'),
]
