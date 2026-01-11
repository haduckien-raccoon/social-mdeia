# apps/friends/templatetags/friend_tags.py
from django import template
from apps.friends.services import get_friend_status
from apps.friends.models import FriendRequest

register = template.Library()

@register.simple_tag
def check_relation(user, target_user):
    return get_friend_status(user, target_user)

@register.simple_tag
def get_request_id(from_user, to_user):
    req = FriendRequest.objects.filter(from_user=from_user, to_user=to_user, status='pending').first()
    print("Debug get_request_id:", from_user, to_user, req)
    return req.id if req else None

# --- THÊM ĐOẠN NÀY ---
@register.filter
def get_avatar(user):
    """
    Lấy avatar an toàn. Nếu lỗi hoặc không có avatar thì trả về ảnh mặc định.
    Cách dùng trong template: {{ user|get_avatar }}
    """
    try:
        if hasattr(user, 'userprofile') and user.userprofile.avatar:
            return user.userprofile.avatar.url
    except Exception:
        pass
    return "https://ui-avatars.com/api/?name=" + user.username + "&background=random"
# ---------------------