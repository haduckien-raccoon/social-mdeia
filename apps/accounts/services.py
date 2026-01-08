import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import RefreshToken, PasswordResetToken
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import User, EmailVerificationToken
from django.conf import settings

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'

def create_jwt_pair_for_user(user):
    access_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    refresh_payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    RefreshToken.objects.create(
        user=user,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    return access_token, refresh_token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_password_reset_token(user):
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=2)
    )
    return token

def register_user(username, email, password):
    # Check trùng
    if User.objects.filter(email=email).exists():
        #in ra log cho dễ debug
        print(f"[DEBUG] Email đã tồn tại: {email}")
        return None, "Email already exists"
    if User.objects.filter(username=username).exists():
        print(f"[DEBUG] Username đã tồn tại: {username}")
        return None, "Username already exists"

    user = User.objects.create_user(username=username, email=email, password=password)
    # Tạo token email
    token = EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1)
    )
    # Gửi mail
    verify_url = f"http://127.0.0.1:8080/accounts/verify-email?token={token.token}"
    send_mail('Verify email', f'Click: {verify_url}', settings.EMAIL_HOST_USER, [user.email])

    return user, None

def verify_email_token(token_value):
    """
    Xác thực token email.
    Trả về: success (bool), message (str)
    """
    if not token_value:
        return False, "Token không được để trống."

    try:
        token = EmailVerificationToken.objects.get(token=token_value, is_used=False)
    except EmailVerificationToken.DoesNotExist:
        return False, "Token không hợp lệ hoặc đã sử dụng."
    except Exception as e:
        print(f"[ERROR] Lỗi khi lấy token: {e}")
        return False, "Đã xảy ra lỗi khi truy xuất token."

    # Kiểm tra hết hạn
    if token.expires_at < timezone.now():
        return False, "Token đã hết hạn."

    try:
        # Kích hoạt user và đánh dấu token đã dùng
        token.is_used = True
        token.save()
        token.user.is_active = True
        token.user.save()
        user = token.user
    except Exception as e:
        print(f"[ERROR] Lỗi khi cập nhật token/user: {e}")
        return False, "Đã xảy ra lỗi khi xác thực email."

    return True, "Email đã được xác thực thành công! Bạn có thể đăng nhập ngay bây giờ.", user