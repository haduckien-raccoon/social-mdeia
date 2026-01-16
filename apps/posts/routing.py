from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/posts/(?P<post_id>\d+)/$', consumers.PostConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
})