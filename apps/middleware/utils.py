# accounts/utils/tokens.py
import jwt
from django.conf import settings
from django.utils import timezone

def decode_access_token(token):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_access_token(user):
    payload = {
        "user_id": user.id,
        "exp": timezone.now() + timezone.timedelta(minutes=15),
        "iat": timezone.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def generate_refresh_token(user):
    payload = {
        "user_id": user.id,
        "exp": timezone.now() + timezone.timedelta(days=7),
        "iat": timezone.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def generate_jwt_pair_for_user(user):
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    return access_token, refresh_token
