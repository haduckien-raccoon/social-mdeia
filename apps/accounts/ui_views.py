from django.views.generic import TemplateView

class RegisterPageView(TemplateView):
    template_name = "accounts/register.html"

class LoginPageView(TemplateView):
    template_name = "accounts/login.html"

class ForgotPasswordPageView(TemplateView):
    template_name = "accounts/forgot_password.html"

class ResetPasswordPageView(TemplateView):
    template_name = "accounts/reset_password.html"
