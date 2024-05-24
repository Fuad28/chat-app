import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PingPongConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        return await super().disconnect(code)
    
    async def receive(self, text_data=None, bytes_data=None):
        text_data= json.loads(text_data)
        if text_data["message"] == "ping":
            await self.send(text_data= json.dumps({"message": "pong"}))        
    

