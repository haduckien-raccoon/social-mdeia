from django.db.models import Q
from apps.accounts.models import User
from .models import FriendRequest, Friend

# -------------------------------
# Helper
# -------------------------------
def get_friend_status(user, target_user):
    if user.id == target_user.id:
        return "self"

    from apps.friends.models import FriendRequest, Friend

    # Check friend
    if Friend.objects.filter(user=user, friend=target_user).exists() or \
       Friend.objects.filter(user=target_user, friend=user).exists():
        return "accepted"

    # Nếu user gửi request
    req = FriendRequest.objects.filter(from_user=user, to_user=target_user).first()
    if req:
        if req.status == FriendRequest.STATUS_PENDING:
            return "pending_sent"  # thêm trạng thái mới
        elif req.status == FriendRequest.STATUS_REJECTED:
            return "rejected"
        elif req.status == FriendRequest.STATUS_ACCEPTED:
            return "accepted"

    # Nếu user nhận request
    req = FriendRequest.objects.filter(from_user=target_user, to_user=user).first()
    if req:
        if req.status == FriendRequest.STATUS_PENDING:
            return "pending_received"
        elif req.status == FriendRequest.STATUS_REJECTED:
            return "none"  # người nhận thấy reject -> nothing
        elif req.status == FriendRequest.STATUS_ACCEPTED:
            return "accepted"

    return "none"

# -------------------------------
# Friend Request Actions
# -------------------------------
def send_friend_request(from_user, to_user):
    if from_user.id == to_user.id:
        return None, "You cannot send friend request to yourself."
    existing = FriendRequest.objects.filter(from_user=from_user, to_user=to_user).first()
    if existing:
        if existing.status == 'pending':
            return None, "Friend request already pending."
        if existing.status == 'accepted':
            return None, "You are already friends."
        if existing.status == 'rejected':
            existing.status = 'pending'
            existing.save()
            return existing, None

    fr = FriendRequest.objects.create(from_user=from_user, to_user=to_user, status='pending')
    return fr, None


def accept_friend_request(user, request_id):
    try:
        fr = FriendRequest.objects.get(id=request_id, to_user=user, status='pending')
        fr.status = 'accepted'
        fr.save()
        # tạo 2 bản ghi Friend (A,B) & (B,A)
        Friend.objects.get_or_create(user=fr.from_user, friend=fr.to_user)
        Friend.objects.get_or_create(user=fr.to_user, friend=fr.from_user)
        return True, "Friend request accepted."
    except FriendRequest.DoesNotExist:
        return False, "Request not found or permission denied."


def reject_friend_request(user, request_id):
    try:
        fr = FriendRequest.objects.get(id=request_id, to_user=user, status='pending')
        fr.status = 'rejected'
        fr.save()
        return True, "Friend request rejected."
    except FriendRequest.DoesNotExist:
        return False, "Request not found."


def unfriend_user(user, target_user):
    Friend.objects.filter(user=user, friend=target_user).delete()
    Friend.objects.filter(user=target_user, friend=user).delete()
    FriendRequest.objects.filter(
        Q(from_user=user, to_user=target_user) | Q(from_user=target_user, to_user=user),
        status='accepted'
    ).delete()
    return True, "Unfriended successfully."


# -------------------------------
# Lists
# -------------------------------
def get_friend_list(user):
    friends = Friend.objects.filter(user=user).select_related('friend')
    return [f.friend for f in friends]


def get_pending_requests(user):
    return FriendRequest.objects.filter(to_user=user, status='pending').select_related('from_user')

def cancel_friend_request(user, request_id):
    """Người gửi hủy lời mời"""
    try:
        fr = FriendRequest.objects.get(id=request_id, from_user=user, status="pending")
        fr.delete()
        return True, "Friend request cancelled."
    except FriendRequest.DoesNotExist:
        return False, "Cannot cancel request."

def get_friend_suggestions(user, limit=10):
    """Gợi ý bạn bè dựa trên bạn của bạn bè"""
    current_friends = set(f.id for f in get_friend_list(user))
    current_friends.add(user.id)
    suggestions = User.objects.exclude(id__in=current_friends)[:limit]
    return suggestions
