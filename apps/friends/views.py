# apps/friends/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import User, UserProfile
from .services import *

# -------------------------------
# Debug / Friend List View
# -------------------------------
def friend_list_view(request):
    user = request.user
    if not user or not isinstance(user, User):
        messages.error(request, "User not logged in.")
        return redirect("login")

    friends = get_friend_list(user)
    profile = UserProfile.objects.filter(user=user).first()
    pending_requests = get_pending_requests(user)
    suggestions = get_friend_suggestions(user)

    context = {
        "user": user,
        "profile": profile,
        "friends": friends,
        "pending_requests": pending_requests,
        "suggestions": suggestions,
        "get_friend_status": get_friend_status,
    }
    return render(request, "friends/debug_friend_list.html", context)


# -------------------------------
# Send / Accept / Reject / Unfriend / Cancel
# -------------------------------
@csrf_exempt
def send_request_view(request, user_id):
    if request.method == "POST":
        user = request.user
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("friends:list")
        _, error = send_friend_request(user, target_user)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Friend request sent.")
    return redirect("friends:list")


@csrf_exempt
def accept_request_view(request, request_id):
    if request.method == "POST":
        user = request.user
        success, msg = accept_friend_request(user, request_id)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect("friends:list")


@csrf_exempt
def reject_request_view(request, request_id):
    if request.method == "POST":
        user = request.user
        success, msg = reject_friend_request(user, request_id)
        if success:
            messages.info(request, msg)
        else:
            messages.error(request, msg)
    return redirect("friends:list")


@csrf_exempt
def unfriend_view(request, user_id):
    if request.method == "POST":
        user = request.user
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("friends:list")
        unfriend_user(user, target_user)
        messages.warning(request, "Unfriended successfully.")
    return redirect("friends:list")


# -------------------------------
# Cancel Friend Request (NEW)
# -------------------------------
@csrf_exempt
def cancel_request_view(request, request_id):
    """
    Hủy friend request đã gửi
    """
    user = request.user
    try:
        from apps.friends.models import FriendRequest
        req = FriendRequest.objects.get(id=request_id, from_user=user, status=FriendRequest.STATUS_PENDING)
        req.delete()
        messages.success(request, "Friend request canceled.")
    except FriendRequest.DoesNotExist:
        messages.error(request, "Friend request not found or cannot be canceled.")
    
    from django.shortcuts import redirect
    return redirect("friends:list")


