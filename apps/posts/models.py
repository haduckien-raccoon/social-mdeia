from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
from apps.core.models import *
import uuid
import os
from django.core.exceptions import ValidationError

# =====================
# ENUMS / CHOICES
# =====================
class PostPrivacy(models.TextChoices):
    PUBLIC = "public", "Public"
    FRIENDS = "friends", "Friends"
    ONLY_ME = "only_me", "Only Me"

class ReactionType(models.TextChoices):
    LIKE = "like", "Like"
    LOVE = "love", "Love"
    HAHA = "haha", "Haha"
    SAD = "sad", "Sad"
    ANGRY = "angry", "Angry"

class ContentStatus(models.TextChoices):
    NORMAL = "normal", "Normal"
    FLAGGED = "flagged", "Flagged"
    BLOCKED = "blocked", "Blocked"
    DELETED = "deleted", "Deleted"

class ReportTargetType(models.TextChoices):
    POST = "post", "Post"
    COMMENT = "comment", "Comment"

# =====================
# POST MODELS
# =====================
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    privacy = models.CharField(max_length=20, choices=PostPrivacy.choices, default=PostPrivacy.PUBLIC)
    status = models.CharField(max_length=20, choices=ContentStatus.choices, default=ContentStatus.NORMAL)

    # Settings
    is_comment_enabled = models.BooleanField(default=True)
    hide_reaction_count = models.BooleanField(default=False)
    hide_comment_count = models.BooleanField(default=False)

    # AI & Moderation
    risk_score = models.FloatField(default=0)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def soft_delete(self):
        self.is_deleted = True
        self.status = ContentStatus.DELETED
        self.save(update_fields=["is_deleted", "status"])

    def __str__(self):
        return f"Post {self.id} by {self.author}"

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="posts/images/")
    order = models.PositiveIntegerField(default=0)

class PostFile(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="posts/files/")
    filename = models.CharField(max_length=255)

class PostTagUser(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="tagged_users")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class PostHashtag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="hashtags")
    tag = models.CharField(max_length=50, db_index=True)

# =====================
# COMMENT (MAX DEPTH = 7)
# =====================
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField(default=1)
    content = models.TextField()

    status = models.CharField(max_length=20, choices=ContentStatus.choices, default=ContentStatus.NORMAL)
    risk_score = models.FloatField(default=0)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.parent and self.parent.level >= 7:
            raise ValidationError("Max comment depth is 7")

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.status = ContentStatus.DELETED
        self.save(update_fields=["is_deleted", "status"])

# =====================
# REACTION (POST + COMMENT)
# =====================
class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=ReactionType.choices)
    
    # Manual Polymorphic (Post or Comment)
    target_type = models.CharField(max_length=10, choices=ReportTargetType.choices)
    target_id = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "target_type", "target_id")

# =====================
# REPORT
# =====================
class ReportReason(models.Model):
    name = models.CharField(max_length=255)
    is_system = models.BooleanField(default=True)

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=10, choices=ReportTargetType.choices)
    target_id = models.PositiveIntegerField()
    reason = models.ForeignKey(ReportReason, on_delete=models.SET_NULL, null=True, blank=True)
    custom_reason = models.TextField(blank=True)

    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

# =====================
# SHARE POST
# =====================
class PostShare(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    new_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shared_post")
    created_at = models.DateTimeField(auto_now_add=True)

class Mention(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="mentions")
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE)
    commanet = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class 