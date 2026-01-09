from django.db.models import Q
from .models import Friendship
from django.contrib.auth import get_user_model

User = get_user_model()

def get_friendship(user1, user2):
    """Tìm mối quan hệ giữa 2 người bất kể chiều nào"""
    return Friendship.objects.filter(
        Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1)
    ).first()

def send_friend_request(from_user, to_user_id):
    if from_user.id == int(to_user_id):
        return None, "You cannot send a friend request to yourself."

    try:
        to_user = User.objects.get(id=to_user_id)
    except User.DoesNotExist:
        return None, "User not found."

    # Check xem đã có quan hệ chưa (kể cả chiều ngược lại)
    existing_relation = get_friendship(from_user, to_user)

    if existing_relation:
        if existing_relation.status == 'accepted':
            return None, "You are already friends."
        if existing_relation.status == 'pending':
            return None, "A friend request is already pending."
        if existing_relation.status == 'rejected':
            # Nếu bị reject trước đó, có thể cho phép gửi lại hoặc không.
            # Ở đây ta cho phép gửi lại bằng cách update record cũ
            existing_relation.status = 'pending'
            existing_relation.from_user = from_user # Reset người gửi là người hiện tại
            existing_relation.to_user = to_user
            existing_relation.save()
            return existing_relation, None

    # Tạo mới
    friendship = Friendship.objects.create(from_user=from_user, to_user=to_user, status='pending')
    return friendship, None

def accept_friend_request(user, request_id):
    try:
        # Chỉ người nhận (to_user) mới được accept
        friendship = Friendship.objects.get(id=request_id, to_user=user, status='pending')
        friendship.status = 'accepted'
        friendship.save()
        return True, "Friend request accepted."
    except Friendship.DoesNotExist:
        return False, "Request not found or you don't have permission."

def reject_friend_request(user, request_id):
    try:
        friendship = Friendship.objects.get(id=request_id, to_user=user, status='pending')
        friendship.status = 'rejected'
        friendship.save()
        return True, "Friend request rejected."
    except Friendship.DoesNotExist:
        return False, "Request not found."

def unfriend_user(user, target_user_id):
    try:
        target_user = User.objects.get(id=target_user_id)
        friendship = get_friendship(user, target_user)
        
        if friendship and friendship.status == 'accepted':
            friendship.delete() # Xóa hẳn record để sau này có thể kết bạn lại từ đầu
            return True, "Unfriended successfully."
        return False, "You are not friends."
    except Exception as e:
        return False, str(e)

def get_friend_list(user):
    """Lấy danh sách bạn bè đã accept (cả 2 chiều)"""
    friends_rel = Friendship.objects.filter(
        (Q(from_user=user) | Q(to_user=user)) & Q(status='accepted')
    ).select_related('from_user', 'to_user')

    friends = []
    friend_ids = []
    for rel in friends_rel:
        if rel.from_user == user:
            friends.append(rel.to_user)
            friend_ids.append(rel.to_user.id)
        else:
            friends.append(rel.from_user)
            friend_ids.append(rel.from_user.id)
            
    return friends, friend_ids

def get_pending_requests(user):
    """Lấy danh sách lời mời kết bạn ĐANG CHỜ TÔI DUYỆT"""
    return Friendship.objects.filter(to_user=user, status='pending').select_related('from_user')

def get_friend_suggestions(user):
    """
    Gợi ý bạn bè dựa trên: Bạn của bạn bè (Mutual Friends).
    """
    current_friends, current_friend_ids = get_friend_list(user)
    
    # Nếu chưa có bạn bè, gợi ý random (trừ bản thân)
    if not current_friend_ids:
        return User.objects.exclude(id=user.id)[:5]

    # Tìm bạn của những người bạn hiện tại
    # Logic: Lấy tất cả quan hệ accepted của friends tôi, loại trừ tôi và những người đã là bạn tôi
    suggestions = []
    checked_ids = set(current_friend_ids)
    checked_ids.add(user.id) # Không gợi ý chính mình

    # Lấy các quan hệ của bạn bè tôi
    friends_of_friends_rel = Friendship.objects.filter(
        (Q(from_user__in=current_friends) | Q(to_user__in=current_friends)) & Q(status='accepted')
    ).distinct()

    for rel in friends_of_friends_rel:
        potential_friend = None
        if rel.from_user in current_friends:
            potential_friend = rel.to_user
        else:
            potential_friend = rel.from_user
        
        # Nếu người này chưa nằm trong danh sách bạn bè và không phải là tôi
        if potential_friend.id not in checked_ids:
            suggestions.append(potential_friend)
            checked_ids.add(potential_friend.id) # Tránh duplicate trong list gợi ý

    return suggestions[:10] # Trả về tối đa 10 gợi ý