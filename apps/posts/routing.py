from channels.routing import re_path   # ✅ ĐÚNG
from .consumers import *

websocket_urlpatterns = [
    re_path(r"ws/feed/$", FeedConsumer.as_asgi()),
    re_path(r"ws/post/(?P<post_id>\d+)/$", PostConsumer.as_asgi()),
    re_path(r"ws/comment/(?P<comment_id>\d+)/$", CommentConsumer.as_asgi()),
]
