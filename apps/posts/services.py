from hashlib import new
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.accounts.models import *
from apps.friends.models import *
from apps.posts.models import *
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_ws_message(group_name, message_type, data):
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": message_type,
                "data": data
            }
        )
    else:
        print("Channel layer is not available")

def require_owner(user, obj):
    if obj.author != user:
        raise PermissionDenied("You do not have permission to perform this action.")

def require_comment_owner(user, comment):
    if comment.user != user:
        raise PermissionDenied("You do not have permission to perform this action.")

def require_post_owner_or_comment_owner(user, post, comment):
    if comment.user != user and post.author != user:
        raise PermissionDenied("You do not have permission to perform this action.")

def ensure_comment_enable(post):
    if not post.is_comment_enabled:
        raise ValidationError("Comments are disabled for this post.")

@transaction.atomic
def create_post(
    *,
    user,
    content,
    privacy,
    images=None,
    files=None,
    tagged_users=None,
    hashtags=None,
    location_name=None,
):
    post = Post.objects.create(
        author=user,
        content=content.strip() if content else "",
        privacy=privacy,
    )

    # =====================
    # Images
    # =====================
    if images:
        for order, image in enumerate(images):
            PostImage.objects.create(
                post=post,
                image=image,
                order=order
            )

    # =====================
    # Files
    # =====================
    if files:
        for file in files:
            PostFile.objects.create(
                post=post,
                file=file,
                filename=file.name
            )

    # =====================
    # Tagged users
    # =====================
    if tagged_users:
        PostTagUser.objects.bulk_create([
            PostTagUser(post=post, user=user)
            for user in tagged_users
        ], ignore_conflicts=True)

    # =====================
    # Hashtags
    # =====================
    if hashtags:
        for raw_tag in hashtags:
            tag = raw_tag.strip().lower().lstrip("#")
            if not tag:
                continue

            hashtag, _ = Hashtag.objects.get_or_create(tag=tag)
            PostHashtag.objects.get_or_create(
                post=post,
                hashtag=hashtag
            )

    # =====================
    # Location
    # =====================
    if location_name:
        Location.objects.create(
            post=post,
            name=location_name.strip(),
            latitude=0.0,
            longitude=0.0
        )

    return post

@transaction.atomic
def update_post(post, content=None, privacy=None):
    if content is not None:
        post.content = content
    if privacy is not None:
        post.privacy = privacy
    post.updated_at = timezone.now()
    post.save()
    return post

def delete_post(user, post):
    require_owner(user, post)
    post.soft_delete()

def toggle_comments(post, user, enable: bool):
    require_owner(user, post)
    post.is_comment_enabled = enable
    post.save(update_fields=["is_comment_enabled"])
    return post

def toggle_hide_counts(post, user, hide_comment=None, hide_reaction=None):
    require_owner(user, post)
    if hide_comment is not None:
        post.hide_comment_count = hide_comment
    if hide_reaction is not None:
        post.hide_reaction_count = hide_reaction
    post.save()
    return post

def create_comment(user, post, content, parent=None, images=None, files=None):
    ensure_comment_enable(post)

    if parent:
        if parent.post != post:
            raise ValidationError("Parent comment must belong to the same post.")
        if parent.level >= 7:
            raise ValidationError("Max comment depth is 7.")

    comment = Comment.objects.create(
        user=user,
        post=post,
        parent=parent,
        content=content
    )

    if images:
        for order, image in enumerate(images):
            CommentImage.objects.create(comment=comment, image=image, order=order)

    if files:
        for file in files:
            CommentFile.objects.create(comment=comment, file=file, filename=file.name)

    send_ws_message(f"post_{post.id}", "comment_created", {
        "id": comment.id,
        "content": comment.content,
        "user": comment.user.username,
        "user_initial": comment.user.username[0].upper(),
        "created_at": comment.created_at.strftime("%d/%m %H:%M"),
        "parent_id": parent.id if parent else None,
        "level": comment.level
    })

    return comment

def update_comment(user, comment, content):
    require_comment_owner(user, comment)
    comment.content = content
    comment.updated_at = timezone.now()
    comment.save()
    return comment

def delete_comment(user, comment):
    require_comment_owner(user, comment)
    comment.soft_delete()

def toggle_post_reaction(user, post, reaction_type):
    # 1. Tìm hoặc tạo reaction
    reaction, created = PostReaction.objects.get_or_create(
        user=user,
        post=post,
        defaults={'reaction_type': reaction_type}
    )

    status = "added"
    current_reaction = reaction_type # Loại reaction hiện tại của user

    # 2. Xử lý logic
    if not created:
        if reaction.reaction_type == reaction_type:
            # Nếu bấm lại đúng icon đó -> Xóa (Unlike)
            reaction.delete()
            status = "removed"
            current_reaction = None
        else:
            # Nếu bấm icon khác -> Đổi (Change)
            reaction.reaction_type = reaction_type
            reaction.save(update_fields=['reaction_type'])
            status = "changed"
            current_reaction = reaction_type

    # 3. Tính lại count SAU KHI đã thay đổi DB
    count = post.reactions.count()

    # 4. Gửi WebSocket
    send_ws_message(f"post_{post.id}", "post_reaction", {
        "post_id": post.id,
        "status": status,
        "user": user.username,
        "reaction_type": current_reaction, # Gửi loại reaction hiện tại (hoặc None)
        "count": count
    })
    
    return status

def toggle_comment_reaction(user, comment, reaction_type):
    reaction, created = CommentReaction.objects.get_or_create(
        user=user,
        comment=comment,
        defaults={'reaction_type': reaction_type}
    )

    status = "added"
    current_reaction = reaction_type

    if not created:
        if reaction.reaction_type == reaction_type:
            reaction.delete()
            status = "removed"
            current_reaction = None
        else:
            reaction.reaction_type = reaction_type
            reaction.save(update_fields=['reaction_type'])
            status = "changed"
            current_reaction = reaction_type

    count = comment.reactions.count()

    send_ws_message(f"post_{comment.post.id}", "comment_reaction", {
        "comment_id": comment.id,
        "status": status,
        "user": user.username,
        "reaction_type": current_reaction,
        "count": count
    })
    
    return status

@transaction.atomic
def share_post(user, original_post, caption="", privacy="public"):
    new_post = Post.objects.create(
        author=user,
        content=caption,
        privacy=privacy,
    )

    PostShare.objects.create(
        user=user,  
        original_post=original_post,
        new_post=new_post,
        caption = caption,
        privacy = privacy
    )

    return new_post

def report_target(user, target_type, target_id, reason=None, custom_reason=""):
    report = Report.objects.create(
        reporter=user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        custom_reason=custom_reason
    )
    return report

def tag_user(post, user):
    tag, created = PostTagUser.objects.get_or_create(post=post, user=user)
    return tag

def un_tag_user(post, user):
    tag = PostTagUser.objects.filter(post=post, user=user)
    tag.delete()

def add_hashtags(post, hashtags):
    for tag in hashtags:
        Hashtag.objects.get_or_create(tag=tag)
        PostHashtag.objects.get_or_create(post=post, hashtag=Hashtag.objects.get(tag=tag))

def remove_hashtags(post, hashtags):
    for tag in hashtags:
        hashtag = Hashtag.objects.filter(tag=tag).first()
        if hashtag:
            post_hashtag = PostHashtag.objects.filter(post=post, hashtag=hashtag)
            post_hashtag.delete()

def add_location(post, name, lat, lng):
    location = Location.objects.create(name=name, latitude=lat, longitude=lng)
    post.location = location
    post.save(update_fields=['location'])
    return location

def remove_location(post):
    post.location.delete()
    post.location = None
    post.save(update_fields=['location'])

def  get_public_feed():
    posts = Post.objects.filter(
        privacy="public",
        is_deleted=False
    ).select_related('author').order_by('-created_at')
    return posts

def get_user_feed(user, friends_ids):
    posts = Post.objects.filter(
        is_deleted=False
    ).filter(
        Q(privacy="public") |
        Q(privacy="friends", author__id__in=friends_ids) |
        Q(privacy="only_me", author=user)
    ).select_related('author').order_by('-created_at')
    return posts

def get_friend_ids(user):
    friend_ids = Friend.objects.filter(
        Q(friend_id =user.id) | Q(user_id=user.id)
    ).values_list('friend_id', 'user_id')
    friend_ids_set = set()
    for u1, u2 in friend_ids:
        if u1 != user.id:
            friend_ids_set.add(u1)
        if u2 != user.id:
            friend_ids_set.add(u2)
    return list(friend_ids_set)
    