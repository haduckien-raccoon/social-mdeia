from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .services import (
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    get_friend_list,
    get_pending_requests,
    get_friend_suggestions,
    unfriend_user
)
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def friend_list_view(request):
    friends, _ = get_friend_list(request.user)
    pending_requests = get_pending_requests(request.user)
    suggestions = get_friend_suggestions(request.user)

    context = {
        "friends": friends,
        "pending_requests": pending_requests,
        "suggestions": suggestions
    }
    return render(request, "friends/friend_list.html", context)

@login_required
@csrf_exempt
def send_request_view(request, user_id):
    if request.method == "POST":
        _, error = send_friend_request(request.user, user_id)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Friend request sent!")
    return redirect("friends:list")

@login_required
@csrf_exempt
def accept_request_view(request, request_id):
    if request.method == "POST":
        success, msg = accept_friend_request(request.user, request_id)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect("friends:list")

@login_required
@csrf_exempt
def reject_request_view(request, request_id):
    if request.method == "POST":
        success, msg = reject_friend_request(request.user, request_id)
        if success:
            messages.info(request, msg)
        else:
            messages.error(request, msg)
    return redirect("friends:list")

@login_required
@csrf_exempt
def unfriend_view(request, user_id):
    if request.method == "POST":
        success, msg = unfriend_user(request.user, user_id)
        if success:
            messages.warning(request, msg)
        else:
            messages.error(request, msg)
    return redirect("friends:list")