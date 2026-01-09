# accounts/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("register/", register_view, name="register"),
    path("verify-email/", verify_email_view, name="verify_email"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("profile/", profile_view, name="profile"),
]
