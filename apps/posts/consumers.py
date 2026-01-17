from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class FeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("feed", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("feed", self.channel_name)

    async def receive(self, text_data):
        pass  # This consumer does not expect to receive messages from clients

    async def post_created(self, event):
        post_data = event['post']
        await self.send(text_data=json.dumps({
            'type': 'post_created',
            'post': post_data
        }))
    
class PostConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope["url_route"]["kwargs"]["post_id"]
        self.group_name = f"post_{self.post_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handlers nhận message từ Services -> Gửi xuống Client
    async def post_reaction(self, event):
        await self.send_json({"type": "post_reaction", "data": event["data"]})

    async def comment_created(self, event):
        await self.send_json({"type": "comment_created", "data": event["data"]})

    async def comment_reaction(self, event):
        await self.send_json({"type": "comment_reaction", "data": event["data"]})

    async def comment_deleted(self, event):
        await self.send_json({"type": "comment_deleted", "data": event["data"]})

    async def comment_updated(self, event):
        await self.send_json({"type": "comment_updated", "data": event["data"]})

class CommentConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        self.comment_id = self.scope["url_route"]["kwargs"]["comment_id"]
        self.group_name = f"comment_{self.comment_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def comment_reaction(self, event):
        await self.send_json({
            "type": "comment_reaction",
            "reaction": event
        })