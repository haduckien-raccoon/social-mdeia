# accounts/urls.py
from django.urls import path
from .views import *

app_name = "accounts"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("verify-email/", verify_email_view, name="verify_email"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("profile/", profile_view, name="profile"),
    path("profile/<int:id>/", profile_view, name="profile-other"),
    path("profile/<str:username>/", profile_view, name="profile"),
    path("edit_profile/", edit_profile_view, name="edit_profile"),
    path("update_email/", update_email_view, name="update_email"),
    path("update_username/", update_username_view, name="update_username"),
    path("update_password/", update_password_view, name="update_password"),
]
