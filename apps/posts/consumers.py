from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ReactionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.group_name = f"reaction_{self.post_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def reaction_event(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    