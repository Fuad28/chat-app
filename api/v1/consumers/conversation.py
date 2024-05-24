import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from api.models import Conversation, ConversationMembers, Message

@database_sync_to_async
def get_conversations_details(user_id):
    """ Gets the details of all conversation a user belongs. """
    data= {}

    conversations = Conversation.objects.filter(members= user_id)

    for conversation in conversations:
        joined_at = ConversationMembers.objects.get(
            user_id= user_id, 
            conversation= conversation
        ).joined_at

        unreads= Message.objects.filter(
            conversation= conversation, 
            sent_at__gte= joined_at
            ).exclude(
                seen_by=user_id
            ).count()

        data[conversation.id] = {"unreads": unreads, **conversation.to_dict()}
    
        
    return data

@database_sync_to_async
def is_member_of_conversation(user_id, conversation_id):
    """ DB level validation before a user is added to a channel. """

    return ConversationMembers.objects.filter(
        user_id= user_id, 
        conversation_id= conversation_id
        ).exists()

class ConversationConsumer(AsyncWebsocketConsumer):
    """

    handle create, broadcast and persiste
    handle getting data with paginations
    handle data update and updating redis instance
    handle message delete and removing redis instance
    clean up

    """
    async def connect(self):

        await self.accept()

        self.user_id= self.scope["user"].id

        conversations = Conversation.objects.filter(members= self.user_id)
        for conversation in conversations:
            await self.channel_layer.group_add(conversation.id, self.channel_name)

        
        conversations= await get_conversations_details(self.user_id)
        data= {
            "status": "connected",
            "conversations": conversations
        }
        await self.channel_layer.send(self.channel_name, {"type": "send.message", "data": data})


    async def disconnect(self, close_code):
        conversations = Conversation.objects.filter(members= self.user_id)
        for conversation in conversations:
            await self.channel_layer.group_discard(conversation.id, self.channel_name)

    
    async def send_message(self, event):
        await self.send(text_data= json.dumps({"message": event["data"]}))


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user_id= self.scope["user"].id

        if await is_member_of_conversation(self.user_id, self.conversation_id):
            await self.accept()

        
        conversations= await get_conversations_details(self.user_id) # retrieve cached messages

        data= {
            "status": "connected",
            "conversations": conversations
        }
        await self.channel_layer.send(self.channel_name, {"type": "send.message", "data": data})


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def receive(self, text_data=None, bytes_data=None):
        json_data= json.loads(text_data)
        if json_data["type"] == "message.create":
            await self.channel_layer.group_send(
                self.conversation_id, 
                {"type": "send.message", "data": json_data}
            )
    
    async def send_message(self, event):
        await self.send(text_data= json.dumps({"message": event["data"]}))