import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from api.models import User, Conversation, ConversationMembers, Message

class ConversationConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        await self.accept()

        self.user: User= self.scope["user"]
    
        conversations = await self._get_conversations_details(self.user)
        for conversation_id in conversations:
            await self.channel_layer.group_add(conversation_id, self.channel_name)

        data= {
            "status": "connected",
            "conversations": conversations
        }

        return await self.channel_layer.send(self.channel_name, {"type": "send.message", "message": data})


    async def disconnect(self, close_code):
        conversations = self._get_conversations_details(self.user)
        for conversation_id in conversations:
            await self.channel_layer.group_discard(conversation_id, self.channel_name)

    
    async def send_message(self, event):
        return await self.send(text_data= json.dumps({"message": event["message"]}))
    
    @database_sync_to_async
    def _get_conversations_details(self, user):
        """ Gets the details of all conversation a user belongs. """
        
        data= {}

        conversations = Conversation.objects.filter(members= self.user)

        for conversation in conversations:
            joined_at = ConversationMembers.objects.get(
                user= self.user, 
                conversation= conversation
            ).joined_at

            unreads= Message.objects.filter(
                conversation= conversation, 
                sent_at__gte= joined_at
                ).exclude(
                    seen_by= self.user
                ).count()

            data[str(conversation.id)] = {"unreads": unreads, **conversation.to_dict()}


        return data