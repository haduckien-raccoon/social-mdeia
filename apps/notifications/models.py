from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
from apps.core.models import *


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="actions")
    verb_text = models.CharField(max_length=50)  # liked, commented, replied, mentioned
    target_type = models.CharField(max_length=20)
    target_id = models.PositiveIntegerField()
    target_repr = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verb_code = models.CharField(max_length=50, 
                                 choices = [
                                     ('like_post', 'Like Post'),
                                     ('comment_post', 'Comment Post'),
                                     ('reply_comment', 'Reply Comment'),
                                     ('mention_post', 'Mention Post'),
                                     ('mention_comment', 'Mention Comment'),
                                     ('share_post', 'Share Post'),
                                     ('friend_request', 'Friend Request'),
                                     ('friend_accept', 'Friend Accept'),
                                     
                                 ],)
