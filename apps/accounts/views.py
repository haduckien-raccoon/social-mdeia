from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import User, EmailVerificationToken, RefreshToken, PasswordResetToken
from .serializers import RegisterSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .services import create_jwt_pair_for_user, create_password_reset_token
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

# Register + Email verification
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            verify_url = f"http://127.0.0.1:8000/accounts/verify-email/?token={token.token}"
            send_mail('Verify email', f'Click: {verify_url}', settings.DEFAULT_FROM_EMAIL, [user.email])
            return Response({'message': 'User registered. Check email to verify.'}, status=201)
        return Response(serializer.errors, status=400)

class VerifyEmailView(APIView):
    def get(self, request):
        token_value = request.GET.get('token')
        try:
            token = EmailVerificationToken.objects.get(token=token_value, is_used=False)
        except EmailVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=400)
        if token.expires_at < timezone.now():
            return Response({'error': 'Token expired'}, status=400)
        token.is_used = True
        token.save()
        token.user.is_active = True
        token.user.save()
        return Response({'message': 'Email verified, you can login now'})

# Login
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        if not user.is_active:
            return Response({'error': 'Email not verified'}, status=401)
        access_token, refresh_token = create_jwt_pair_for_user(user)
        response = Response({'message': 'Login successful'})
        response.set_cookie('access', access_token, httponly=True, max_age=900)
        response.set_cookie('refresh', refresh_token, httponly=True, max_age=604800)
        return response

# Logout
class LogoutView(APIView):
    def post(self, request):
        response = Response({'message': 'Logged out'})
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response

# Forgot password
class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'message': 'If email exists, reset link sent'}, status=200)
            token = create_password_reset_token(user)
            reset_url = f"http://127.0.0.1:8000/accounts/reset-password/?token={token.token}"
            send_mail('Reset password', f'Click: {reset_url}', settings.DEFAULT_FROM_EMAIL, [user.email])
            return Response({'message': 'Password reset link sent to email'}, status=200)
        return Response(serializer.errors, status=400)

# Reset password
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            password = serializer.validated_data['password']
            try:
                token = PasswordResetToken.objects.get(token=token_value, is_used=False)
            except PasswordResetToken.DoesNotExist:
                return Response({'error': 'Invalid or used token'}, status=400)
            if token.expires_at < timezone.now():
                return Response({'error': 'Token expired'}, status=400)
            user = token.user
            user.set_password(password)
            user.save()
            token.is_used = True
            token.save()
            return Response({'message': 'Password reset successful'})
        return Response(serializer.errors, status=400)

