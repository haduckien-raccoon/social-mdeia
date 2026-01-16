from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
from apps.core.models import *


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    reference_id = models.PositiveIntegerField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)