import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FeedConsumer(AsyncWebsocketConsumer):
    """
    WebSocket cho bảng tin chung - Nhận thông báo khi có bài viết mới
    """
    async def connect(self):
        await self.channel_layer.group_add("feed_global", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("feed_global", self.channel_name)

    async def feed_update(self, event):
        """
        Nhận event từ services và gửi xuống client
        Event type: "feed_update"
        """
        await self.send(text_data=json.dumps(event["data"]))

class PostConsumer(AsyncWebsocketConsumer):
    """
    WebSocket cho từng bài viết cụ thể
    Xử lý realtime: reactions, comments, comment reactions, updates
    """
    async def connect(self):
        self.post_id = self.scope["url_route"]["kwargs"]["post_id"]
        self.group_name = f"post_{self.post_id}"
        
        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def post_event(self, event):
        """
        Handler chung cho mọi event của post
        Gửi data xuống client qua WebSocket
        """
        await self.send(text_data=json.dumps(event["data"]))