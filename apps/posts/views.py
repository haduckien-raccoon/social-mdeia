from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from apps.posts.models import *
from apps.posts.services import *
from apps.friends.models import Friend
# =====================================================
# FEED VIEWS
# =====================================================
def feed_view(request):
    """Bảng tin cá nhân"""
    friends_ids = get_friend_ids(request.user)
    posts = get_user_feed(request.user, friends_ids)
    
    # Annotate thêm số lượng reactions và comments
    posts = posts.annotate(
        reaction_count=Count('reactions', distinct=True),
        comment_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True)
    )
    
    # Kiểm tra trạng thái reaction của user hiện tại cho POST
    for post in posts:
        reaction = PostReaction.objects.filter(post=post, user=request.user).first()
        post.current_user_reaction = reaction.reaction_type if reaction else None
    
    return render(request, "posts/feed.html", {"posts": posts})

def public_feed_view(request):
    """Bảng tin công khai"""
    posts = get_public_feed()
    posts = posts.annotate(
        reaction_count=Count('reactions', distinct=True),
        comment_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True)
    )
    for post in posts:
        reaction = PostReaction.objects.filter(post=post, user=request.user).first()
        post.current_user_reaction = reaction.reaction_type if reaction else None
    return render(request, "posts/public_feed.html", {"posts": posts})

# =====================================================
# POST DETAIL VIEW (SỬA LẠI PHẦN NÀY)
# =====================================================
def post_detail_view(request, post_id):
    """Chi tiết bài viết"""
    post = get_object_or_404(
        Post.objects.select_related("author").prefetch_related(
            "images", "files", "tagged_users", "hashtags", "reactions"
        ),
        id=post_id,
        is_deleted=False
    )

    # 1. Privacy Check
    if post.privacy == "only_me" and post.author != request.user:
        return HttpResponseForbidden("Bài viết riêng tư")
    if post.privacy == "friends":
        is_friend = Friend.objects.filter(
            Q(user=post.author, friend=request.user) | 
            Q(user=request.user, friend=post.author)
        ).exists()
        if not is_friend and post.author != request.user:
            return HttpResponseForbidden("Chỉ bạn bè mới xem được")

    # 2. Get Comments & Reactions
    # Dùng annotate để đếm like comment ngay trong query (Tối ưu DB)
    comments = (
        Comment.objects
        .filter(post=post, is_deleted=False)
        .select_related("user")
        .prefetch_related("images", "files")
        .annotate(likes_count=Count('reactions')) # Đếm số like
        .order_by("created_at")
    )

    # 3. Lấy trạng thái Like của User hiện tại cho từng Comment
    # Tạo Map: {comment_id: reaction_type}
    comment_reactions = CommentReaction.objects.filter(
        comment__post=post, user=request.user
    ).values_list('comment_id', 'reaction_type')
    
    my_reaction_map = {c_id: r_type for c_id, r_type in comment_reactions}

    # Gán vào từng comment để Template hiển thị
    for c in comments:
        c.index_px = max(0, (c.level - 1) * 20)
        c.current_reaction = my_reaction_map.get(c.id) # ĐỔI TÊN BIẾN Ở ĐÂY CHO KHỚP TEMPLATE

    # 4. Post Reaction của User hiện tại
    post_reaction = PostReaction.objects.filter(post=post, user=request.user).first()
    post.current_user_reaction = post_reaction.reaction_type if post_reaction else None

    # Reaction Breakdown (Thống kê số lượng từng loại reaction)
    reaction_counts = PostReaction.objects.filter(post=post).values('reaction_type').annotate(count=Count('id'))
    reaction_breakdown = {item['reaction_type']: item['count'] for item in reaction_counts}

    context = {
        "post": post,
        "comments": comments,
        "reaction_breakdown": reaction_breakdown,
        "total_reactions": PostReaction.objects.filter(post=post).count(),
        "total_comments": comments.count(),
    }

    return render(request, "posts/post_detail.html", context)
# =====================================================
# POST CRUD
# =====================================================
def create_post_view(request):
    """Tạo bài viết mới"""
    if request.method == "POST":
        content = request.POST.get("content", "")
        privacy = request.POST.get("privacy", "public")

        images = request.FILES.getlist("images")
        #in ra log để debug
        print(f"[DEBUG] Uploaded images: {images}")
        files = request.FILES.getlist("files")
        tagged = request.POST.getlist("tagged_users")
        location = request.POST.get("location", "")

        post = create_post(
            user=request.user,
            content=content,
            privacy=privacy,
            images=images,
            files=files,
            tagged_users=tagged,
            location_name=location
        )

        return redirect("posts:post_detail", post_id=post.id)
    
    # GET request - Show form
    friends = list_people_tag(request.user)
    profile = request.user.profile
    return render(request, "posts/create_post.html", {"friends": friends, "profile": profile})

def edit_post_view(request, post_id):
    """Chỉnh sửa bài viết"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)

    if post.author != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        content = request.POST.get("content")
        privacy = request.POST.get("privacy")
        tag_users = request.POST.getlist("tagged_users")
        location = request.POST.get("location", "")
        
        # 1. Lấy file MỚI upload lên
        images = request.FILES.getlist("images")
        files = request.FILES.getlist("files")
        
        # 2. Lấy danh sách ID CŨ cần xóa (quan trọng)
        delete_image_ids = request.POST.getlist("delete_image_ids")
        delete_file_ids = request.POST.getlist("delete_file_ids")

        print(f"[DEBUG] New Images: {images}")
        print(f"[DEBUG] Delete Img IDs: {delete_image_ids}")

        update_post(
            post, 
            content=content, 
            privacy=privacy, 
            tagged_users=tag_users, 
            images=images, 
            files=files, 
            location_name=location,
            delete_image_ids=delete_image_ids, # Truyền vào service
            delete_file_ids=delete_file_ids    # Truyền vào service
        )
        return redirect("posts:post_detail", post_id=post.id)
    
    friends = list_people_tag(request.user)
    profile = request.user.profile
    return render(request, "posts/edit_post.html", {"post": post, "friends": friends, "profile": profile})

@require_POST
def delete_post_view(request, post_id):
    """Xóa bài viết"""
    post = get_object_or_404(Post, id=post_id)
    delete_post(request.user, post)
    return redirect("posts:feed")

# =====================================================
# COMMENT CRUD (AJAX/REALTIME)
# =====================================================
@require_POST
def create_comment_view(request, post_id):
    """Tạo bình luận mới - Trả về JSON cho AJAX"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Content is required"}, status=400)
    
    parent_id = request.POST.get("parent_id")
    parent = Comment.objects.filter(id=parent_id).first() if parent_id else None

    images = request.FILES.getlist("images")
    files = request.FILES.getlist("files")

    try:
        comment = create_comment(
            user=request.user,
            post=post,
            content=content,
            parent=parent,
            images=images,
            files=files
        )
        
        return JsonResponse({
            "status": "ok",
            "comment_id": comment.id,
            "message": "Comment created successfully"
        })
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
def edit_comment_view(request, comment_id):
    """Chỉnh sửa bình luận"""
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)
    content = request.POST.get("content", "").strip()
    
    if not content:
        return JsonResponse({"error": "Content is required"}, status=400)
    
    try:
        update_comment(request.user, comment, content)
        return JsonResponse({"status": "ok"})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

@require_POST
def delete_comment_view(request, comment_id):
    """Xóa bình luận"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    try:
        delete_comment(request.user, comment)
        return JsonResponse({"status": "ok"})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

# =====================================================
# REACTION VIEWS (AJAX/REALTIME)
# =====================================================
@require_POST
def toggle_post_reaction_view(request, post_id):
    """Toggle reaction cho bài viết"""
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.POST.get("reaction", "like")
    
    result = toggle_post_reaction(request.user, post, reaction_type)
    return JsonResponse(result)

@require_POST
def toggle_comment_reaction_view(request, comment_id):
    """Toggle reaction cho bình luận"""
    comment = get_object_or_404(Comment, id=comment_id)
    reaction_type = request.POST.get("reaction", "like")
    
    result = toggle_comment_reaction(request.user, comment, reaction_type)
    return JsonResponse(result)

# =====================================================
# OTHER ACTIONS
# =====================================================
@require_POST
def share_post_view(request, post_id):
    """Chia sẻ bài viết"""
    original_post = get_object_or_404(Post, id=post_id)
    caption = request.POST.get("caption", "")
    privacy = request.POST.get("privacy", "public")

    new_post = share_post(request.user, original_post, caption, privacy)
    return redirect("posts:post_detail", post_id=new_post.id)

@require_POST
def report_view(request):
    """Báo cáo bài viết hoặc bình luận"""
    target_type = request.POST.get("target_type")
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

@require_POST
def toggle_commenting_view(request, post_id):
    """Bật/tắt bình luận cho bài viết"""
    post = get_object_or_404(Post, id=post_id)
    enable = request.POST.get("enable") == "true"
    
    try:
        toggle_comments(post, request.user, enable)
        return JsonResponse({"success": True})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

@require_POST
def toggle_hide_counts_view(request, post_id):
    """Ẩn/hiện số lượng reactions và comments"""
    post = get_object_or_404(Post, id=post_id)
    hide_comment = request.POST.get("hide_comment")
    hide_reaction = request.POST.get("hide_reaction")

    try:
        toggle_hide_counts(
            post,
            request.user,
            hide_comment=hide_comment == "true" if hide_comment else None,
            hide_reaction=hide_reaction == "true" if hide_reaction else None,
        )
        return JsonResponse({"success": True})
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)