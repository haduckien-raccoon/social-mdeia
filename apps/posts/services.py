from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from .models import (
    Post,
    PostImage,
    PostFile,
    PostPrivacy,
    Comment,
    Reaction,
    PostTagUser,
    PostHashtag
)

User = get_user_model()

# ======================================================
# POST SERVICE
# ======================================================
class PostService:
    """
    Business logic cho Post (MVT)
    """
    @staticmethod
    @transaction.atomic
    def create_post(*, user, content, privacy=PostPrivacy.PUBLIC,
                    images=None, files=None, tagged_users=None, hashtags=None):
        """Create new post with attachments"""

        post = Post.objects.create(
            author=user,
            content=content,
            privacy=privacy,
        )

        # Images
        if images:
            for index, image in enumerate(images):
                PostImage.objects.create(
                    post=post,
                    image=image,
                    order=index,
                )

        # Files
        if files:
            for file in files:
                PostFile.objects.create(
                    post=post,
                    file=file,
                    filename=file.name,
                )

        # Tag users (friends only – validate in view)
        if tagged_users:
            # Lưu ý: tagged_users phải là list các User instance
            PostTagUser.objects.bulk_create([
                PostTagUser(post=post, user=u)
                for u in tagged_users
            ])

        # Hashtags
        if hashtags:
            # Lưu ý: hashtags là list các string
            PostHashtag.objects.bulk_create([
                PostHashtag(post=post, tag=tag.lower())
                for tag in hashtags
            ])

        return post

    @staticmethod
    def update_post(*, user, post: Post, content, privacy):
        """Update post (owner only)"""

        if post.author != user:
            raise PermissionDenied("You are not the owner of this post")

        post.content = content
        post.privacy = privacy
        post.save(update_fields=["content", "privacy", "updated_at"])
        return post

    @staticmethod
    def delete_post(*, user, post: Post):
        """Soft delete post (owner only)"""

        if post.author != user:
            raise PermissionDenied("You are not the owner of this post")

        post.soft_delete()

# ======================================================
# COMMENT SERVICE
# ======================================================
class CommentService:
    """
    Business logic cho Comment (depth <= 7)
    """
    @staticmethod
    def create_comment(*, user, post: Post, content, parent: Comment = None):
        if not post.is_comment_enabled:
            raise ValidationError("Commenting is disabled for this post")

        comment = Comment(
            user=user,
            post=post,
            content=content,
            parent=parent,
        )

        # validate depth <= 7
        comment.full_clean()
        comment.save()
        return comment

    @staticmethod
    def update_comment(*, user, comment: Comment, content):
        if comment.user != user:
            raise PermissionDenied("You are not the owner of this comment")

        comment.content = content
        comment.save(update_fields=["content", "updated_at"])
        return comment

    @staticmethod
    def delete_comment(*, user, comment: Comment):
        # Allow owner of comment OR owner of post to delete
        if comment.user != user and comment.post.author != user:
            raise PermissionDenied("No permission to delete this comment")

        comment.soft_delete()

# ======================================================
# REACTION SERVICE (POST & COMMENT)
# ======================================================
class ReactionService:
    """
    Toggle / change reaction for Post & Comment
    """
    @staticmethod
    def toggle_reaction(*, user, target_type: str, target_id: int, reaction_type: str):
        reaction, created = Reaction.objects.get_or_create(
            user=user,
            target_type=target_type,
            target_id=target_id,
            defaults={"reaction_type": reaction_type},
        )

        # Remove reaction (Toggle off)
        if not created and reaction.reaction_type == reaction_type:
            reaction.delete()
            return None

        # Change reaction type (e.g., Like -> Love)
        reaction.reaction_type = reaction_type
        reaction.save(update_fields=["reaction_type"])
        return reaction