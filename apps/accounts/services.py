import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import RefreshToken, PasswordResetToken
from django.utils import timezone

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
