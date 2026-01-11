import jwt
from django.conf import settings
from django.shortcuts import render
from apps.accounts.models import User

def home(request):
    access_token = request.COOKIES.get("access")

    user = None
    is_authenticated = False

    if access_token:
        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            is_authenticated = True

        except jwt.ExpiredSignatureError:
            pass  # access token hết hạn
        except (jwt.InvalidTokenError, User.DoesNotExist):
            pass

    return render(request, "home.html", {
        "user": user,
        "is_authenticated": is_authenticated
    })

def error_404_view(request, exception):
    return render(request, 'errors/error_404.html', status=404)

def error_500_view(request):
    return render(request, 'errors/error_500.html', status=500)

def error_403_view(request, exception):
    return render(request, 'errors/error_403.html', status=403)
