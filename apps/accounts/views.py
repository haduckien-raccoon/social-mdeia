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
from django.shortcuts import render, redirect

# Register + Email verification
# accounts/views.py
from .services import register_user

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user, error = register_user(username, email, password)
            print(f"[DEBUG] Ket qua dang ky: User={user}, Error={error}")
            if error:
                return Response({'error': error}, status=400)

            return Response({'message': 'User registered. Check email to verify.'}, status=201)
        else:
            # Check the type of serializer.errors
            if isinstance(serializer.errors, dict):
                error = str(list(serializer.errors.values()))
            else:
                # Handle the custom object
                error = str(serializer.errors.get('message', 'Unknown error'))
            print(f"[DEBUG] Loi serializer (string): {error}")
            return Response({'error': serializer.errors}, status=400)

# Login
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        print(f"[DEBUG] Dang nhap voi email: {email}, mat khau: {password}")

        # Sử dụng đúng tên field với USERNAME_FIELD
        user = authenticate(request, username=email, password=password)

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
            reset_url = f"http://127.0.0.1:8080/accounts/api/reset-password/?token={token.token}"
            send_mail('Reset password', f'Click: {reset_url}', settings.EMAIL_HOST_USER, [user.email])
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

