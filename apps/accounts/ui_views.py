from django.shortcuts import render
from django.views.generic import TemplateView
from .models import EmailVerificationToken, User
from .services import verify_email_token

class RegisterPageView(TemplateView):
    template_name = "accounts/register.html"

class LoginPageView(TemplateView):
    template_name = "accounts/login.html"

class ForgotPasswordPageView(TemplateView):
    template_name = "accounts/forgot_password.html"

class ResetPasswordPageView(TemplateView):
    template_name = "accounts/reset_password.html"

from django.views.generic import TemplateView
from django.shortcuts import redirect
from .services import verify_email_token

class VerifyEmailView(TemplateView):
    template_name = "accounts/email_verification.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token_value = self.request.GET.get('token')
        print(f"[DEBUG] Token nhan duoc: {token_value}")
        result = verify_email_token(token_value)
        if len(result) == 3:
            success, message, user = result
        else:
            success, message = result
            user = None
        print(f"[DEBUG] Ket qua xac minh: {success}, Thong diep: {message}")
        context['success'] = success
        context['message'] = message
        context['user'] = user
        return context
