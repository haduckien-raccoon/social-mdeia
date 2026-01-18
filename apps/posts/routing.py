# from channels.routing import re_path   # ✅ ĐÚNG
# from .consumers import *

# websocket_urlpatterns = [
#     re_path(r"ws/feed/$", FeedConsumer.as_asgi()),
#     re_path(r"ws/post/(?P<post_id>\d+)/$", PostConsumer.as_asgi()),
#     re_path(r"ws/comment/(?P<comment_id>\d+)/$", CommentConsumer.as_asgi()),
# ]

from django.urls import re_path
from apps.posts import consumers

websocket_urlpatterns = [
    # Kênh cho Feed (Bảng tin chung)
    # Nhận thông báo khi có bài viết mới
    re_path(r"ws/feed/$", consumers.FeedConsumer.as_asgi()),
    
    # Kênh cho chi tiết bài viết
    # Nhận realtime: reactions, comments, comment reactions, updates
    re_path(r"ws/post/(?P<post_id>\d+)/$", consumers.PostConsumer.as_asgi()),
]