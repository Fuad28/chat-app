import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PingPongConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        pass
    
    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data= json.loads(text_data)
        except Exception as e:
            return await self.send(text_data= json.dumps({"error": "Invalid data"}))


        return await self.send(text_data= "pong")          
    

