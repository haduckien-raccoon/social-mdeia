from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
)
from . import ui_views

urlpatterns = [
    # API endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # UI pages
    path('register-page/', ui_views.RegisterPageView.as_view(), name='register-page'),
    path('login-page/', ui_views.LoginPageView.as_view(), name='login-page'),
    path('forgot-password-page/', ui_views.ForgotPasswordPageView.as_view(), name='forgot-password-page'),
    path('reset-password-page/', ui_views.ResetPasswordPageView.as_view(), name='reset-password-page'),
]
