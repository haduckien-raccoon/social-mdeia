# apps/accounts/middleware.py
import jwt
from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from apps.accounts.models import RefreshToken, User
from apps.middleware.utils import generate_access_token
from django.contrib.auth import login



PUBLIC_PATHS = [
    "/accounts/login/",
    "/accounts/register/",
    "/accounts/verify-email/",
    "/accounts/verify-email",
    "/accounts/forgot-password/",
    "/accounts/reset-password/",
    "/accounts/reset-password",
    "/admin"
]

class JWTAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Bỏ qua route public
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            return None

        access = request.COOKIES.get("access")
        refresh = request.COOKIES.get("refresh")

        # ❌ Không có token nào
        if not access and not refresh:
            return redirect("/accounts/login/")

        # 🟡 Có refresh nhưng không có access
        if refresh and not access:
            return self._refresh_access_token(request, refresh)

        # ✅ Có access nhưng không có refresh check db xem refresh có còn hợp lệ ko để yên tâm
        if access and not refresh:
            return self._authenticate_access(request, access)

        # ✅ Có đủ cả hai
        return self._authenticate_access(request, access, refresh, require_refresh=True)

    # ------------------------------------------------

    def _authenticate_access(self, request, access, refresh=None, require_refresh=True):
        try:
            payload = jwt.decode(
                access,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")

            user = User.objects.get(id=user_id)

            # Nếu yêu cầu kiểm tra refresh, đảm bảo refresh hợp lệ trong DB
            if require_refresh:
                if not refresh:
                    return redirect("/accounts/login/")
                if not RefreshToken.objects.filter(
                    user=user,
                    token=refresh,
                    is_revoked=False,
                    expires_at__gt=timezone.now()
                ).exists():
                    return redirect("/accounts/login/")

            request.user = user
            request._cached_user = user
            return None

        except jwt.ExpiredSignatureError:
            if refresh:
                return self._refresh_access_token(request, refresh)
            return redirect("/accounts/login/")
        except Exception:
            return redirect("/accounts/login/")

    # ------------------------------------------------

    def _refresh_access_token(self, request, refresh):
        try:
            rt = RefreshToken.objects.get(
                token=refresh,
                is_revoked=False,
                expires_at__gt=timezone.now()
            )

            user = rt.user
            new_access = generate_access_token(user)

            request.user = user
            request._cached_user = user

            response = redirect(request.path)
            response.set_cookie(
                "access",
                new_access,
                httponly=True,
                max_age=5 * 60,
                samesite="Lax"
            )
            request.user = user
            return response

        except RefreshToken.DoesNotExist:
            return redirect("/accounts/login/")
        except Exception:
            return redirect("/accounts/login/")