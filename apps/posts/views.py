from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from apps.posts.models import *
from apps.posts.services import *

def create_post_view(request):
    if request.method == "POST":
        content = request.POST.get("content", "")
        privacy = request.POST.get("privacy", "public")

        images = request.FILES.getlist("images")
        files = request.FILES.getlist("files")

        post = create_post(
            user=request.user,
            content=content,
            privacy=privacy,
            images=images,
            files=files
        )

        return redirect("posts:post_detail", post_id=post.id)

    return render(request, "posts/create_post.html")


def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_deleted=False)

    if post.author != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        content = request.POST.get("content")
        privacy = request.POST.get("privacy")

        update_post(post, content=content, privacy=privacy)
        return redirect("posts:post_detail", post_id=post.id)

    return render(request, "posts/edit_post.html", {"post": post})


def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    delete_post(request.user, post)
    return redirect("posts:feed")

def post_detail_view(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author")
        .prefetch_related(
            "images",
            "files",
            "tagged_users",
            "hashtags",
        ),
        id=post_id,
        is_deleted=False
    )

    # =====================
    # PRIVACY CHECK
    # =====================
    if post.privacy == "only_me" and post.author != request.user:
        return HttpResponseForbidden("Private post")

    if post.privacy == "friends":
        is_friend = Friend.objects.filter(
            user=post.author,
            friend=request.user
        ).exists()
        if not is_friend and post.author != request.user:
            return HttpResponseForbidden("Friends only")

    # =====================
    # COMMENTS (TREE)
    # =====================
    comments = (
        Comment.objects
        .filter(post=post, is_deleted=False)
        .select_related("user")
        .prefetch_related(
            "images",
            "files",
            "reactions"
        )
        .order_by("created_at")
    )

    for c in comments:
        c.index_px = max(0, (c.level-1) * 20)  # Thụt lề theo level

    # =====================
    # REACTIONS
    # =====================
    post_reactions = PostReaction.objects.filter(post=post)

    user_post_reaction = post_reactions.filter(
        user=request.user
    ).first()

    # =====================
    # COMMENT REACTION MAP
    # =====================
    comment_reaction_map = {}
    for r in CommentReaction.objects.filter(
        comment__post=post,
        user=request.user
    ):
        comment_reaction_map[r.id] = r.reaction_type
        print("MAP:", comment_reaction_map)

    context = {
        "post": post,
        "comments": comments,
        "post_reactions": post_reactions,
        "user_post_reaction": user_post_reaction,
        "comment_reaction_map": comment_reaction_map,
    }

    return render(request, "posts/post_detail.html", context)

def toggle_commenting_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    enable = request.POST.get("enable") == "true"
    toggle_comments(post, request.user, enable)
    return JsonResponse({"success": True})


def toggle_hide_counts_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    hide_comment = request.POST.get("hide_comment")
    hide_reaction = request.POST.get("hide_reaction")

    toggle_hide_counts(
        post,
        request.user,
        hide_comment=hide_comment == "true" if hide_comment else None,
        hide_reaction=hide_reaction == "true" if hide_reaction else None,
    )
    return JsonResponse({"success": True})

def create_comment_view(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_deleted=False)

    content = request.POST.get("content", "")
    parent_id = request.POST.get("parent_id")

    parent = Comment.objects.filter(id=parent_id).first() if parent_id else None

    images = request.FILES.getlist("images")
    files = request.FILES.getlist("files")

    comment = create_comment(
        user=request.user,
        post=post,
        content=content,
        parent=parent,
        images=images,
        files=files
    )

    return JsonResponse({
        "id": comment.id,
        "content": comment.content,
        "user": comment.user.username,
        "parent": parent.id if parent else None
    })


def edit_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    content = request.POST.get("content")
    update_comment(request.user, comment, content)
    return JsonResponse({"success": True})

def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    delete_comment(request.user, comment)
    return JsonResponse({"success": True})

def toggle_post_reaction_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.POST.get("reaction")
    status = toggle_post_reaction(request.user, post, reaction_type)
    return JsonResponse({"status": status})


def toggle_comment_reaction_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reaction_type = request.POST.get("reaction")
    status = toggle_comment_reaction(request.user, comment, reaction_type)
    return JsonResponse({"status": status})

def share_post_view(request, post_id):
    original_post = get_object_or_404(Post, id=post_id)
    caption = request.POST.get("caption", "")
    privacy = request.POST.get("privacy", "public")

    new_post = share_post(request.user, original_post, caption, privacy)
    return redirect("posts:post_detail", post_id=new_post.id)

def report_view(request):
    target_type = request.POST.get("target_type")  # post / comment
    target_id = request.POST.get("target_id")
    reason = request.POST.get("reason")
    custom_reason = request.POST.get("custom_reason", "")

    report_target(
        user=request.user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        custom_reason=custom_reason
    )
    return JsonResponse({"success": True})

def feed_view(request):
    friends_ids = get_friend_ids(request.user)
    posts = get_user_feed(request.user, friends_ids)
    return render(request, "posts/feed.html", {"posts": posts})


def public_feed_view(request):
    posts = get_public_feed()
    return render(request, "posts/public_feed.html", {"posts": posts})