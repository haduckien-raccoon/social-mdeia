from django.urls import path
from .views import (
    RegisterView,
    # VerifyEmailView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
)
from . import ui_views

urlpatterns = [
    # API endpoints
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    # UI pages
    path('register/', ui_views.RegisterPageView.as_view(), name='register-page'),
    path('login/', ui_views.LoginPageView.as_view(), name='login-page'),
    path('forgot-password/', ui_views.ForgotPasswordPageView.as_view(), name='forgot-password-page'),
    path('reset-password/', ui_views.ResetPasswordPageView.as_view(), name='reset-password-page'),
    path('verify-email/', ui_views.VerifyEmailView.as_view(), name='verify-email'),
]
