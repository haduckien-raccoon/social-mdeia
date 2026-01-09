# apps/friends/templatetags/friend_extras.py
from django import template
from apps.friends.services import get_friend_status

register = template.Library()

@register.simple_tag
def friend_status(user, target_user):
    return get_friend_status(user, target_user)
