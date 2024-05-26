import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from api.services import redis_client
from api.models import User, Conversation, ConversationMembers, Message
from api.v1.serializers.conversation import CreateUpdateMessageSerializer, MessageSerializer

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

class MessageConsumer(AsyncWebsocketConsumer):
        
    async def connect(self):
        try:
            self.user: User= self.scope["user"]
            self.conversation: Conversation = await self._is_valid_conversation_id(
                self.scope['url_route']['kwargs'].get('conversation_id')
            )

            if not self.conversation:
                await self.accept()
                await self.close(code= 4401, reason= "conversation doesn't exist")

            if not await self._is_member_of_conversation():
                await self.accept()
                return await self.close(code= 4403, reason= "Unauthorized")
            
            await self.channel_layer.group_add(str(self.conversation.id), self.channel_name)
            
            await self.accept()
            conversations= await self._messages_list()

            data= {
                "status": "connected",
                "conversations": conversations
            }

            await self.channel_layer.send(self.channel_name, {"type": "send.message", "data": data})
        
        except Exception as e:
            print(e)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.conversation.id, 
            self.channel_name
        )
    
    async def receive(self, text_data=None, bytes_data=None):
        
        data: dict= json.loads(text_data)
        if data.pop("type", None):
            return await self.send_message(data)

        action = data.pop("action", None)
        
        if action == "create":
            return await self.handle_create(data)
        
        if action == "update":
            await self.handle_update(data)
        
        if action == "delete":
            return await self.handle_delete(data)
        
        if action == "list":
            return await self.handle_list(data)
        
        if action == "get":
            return await self.handle_get(data)

        return await self.handle_error({"message": f"type {action} is invalid"})

    async def send_group(self, message):

        return await self.channel_layer.group_send(
            str(self.conversation.id), 
            {"type": "send.message", "message": message}
        )   

    async def send_channel(self, message):
        return await self.channel_layer.send(
            self.channel_name, 
            {"type": "send.message", "message": message}
        )    

    async def send_message(self, event):
        return await self.send(text_data= json.dumps(event))

    async def handle_create(self, data):
        serializer= CreateUpdateMessageSerializer(
            data= data, 
            context= {"user": self.user, "conversation_id": self.conversation.id}
        )
        if not serializer.is_valid():
            return await self.handle_error(serializer.errors)
        
        message: Message = await self._save_serializer(serializer)
        self._redis_store_message(self.conversation.id, message.to_dict())
        
        return await self.send_group(message.to_dict())

    async def handle_update(self, data):
        message: Message = await self._validate_message_id(data.get("message_id"))
        if not message:
            self.send_channel("message doesn't exist")

        if self._is_message_sender(self.user, message):
            serializer= MessageSerializer(data= data, instance= message)
            if not serializer.is_valid():
                return await self.handle_error(serializer.errors)

            message: Message= serializer.save()

            self._redis_update_message(
                self.conversation.id, 
                message.id,
                message.to_dict()
            )
            
            self.send_group(message.to_dict())
        
        return await self.send_channel("Forbidden")

    async def handle_delete(self, data):
        message: Message = await self._validate_message_id(data.get("message_id"))
        if not message:
            self.send_channel("message doesn't exist")

        is_message_sender_= await self._is_message_sender(message)
        is_conversation_admin_= self._is_conversation_admin()
        
        if  is_message_sender_ or is_conversation_admin_:
            message.delete()
            self._redis_delete_message(self.conversation.id, message.id)
            self.send_group("Deleted")
        
        self.send_channel("Forbidden")

    async def handle_list(self, data):
        page_number = data.get('page_number', 1)
        page_size = data.get('page_size', 50)
        paginated_messages= await self._messages_list(page_number, page_size)

        self.send_channel({'messages': paginated_messages})

    async def handle_error(self, message):
        await self.channel_layer.send(
            self.channel_name, 
            {"type": "send.message", "message": message}
        )    

    @database_sync_to_async
    def _is_member_of_conversation(self) -> bool:
        """ DB level validation before a user is added to a channel. """
        
        return self.conversation.members.filter(id= self.user.id).exists()

    @database_sync_to_async
    def _is_message_sender(self, message: Message) -> bool:
        """ Checks if user is message sender. """

        return message.sent_by == self.user

    @database_sync_to_async
    def _is_conversation_admin(self) -> bool:
        """ Checks if user is message sender. """

        return ConversationMembers.objects.filter(
            conversation= self.conversation,
            user= self.user
        ).exists()

    @database_sync_to_async
    def _is_valid_conversation_id(self, conversation_id) -> bool:
        """ Checks if user is message sender. """

        conversation_qs = Conversation.objects.filter(id= conversation_id)
        if conversation_qs.exists():
            return conversation_qs.first()

    @database_sync_to_async
    def _validate_message_id(self, message_id) -> bool:
        """ Checks if user is message sender. """

        message_qs = Message.objects.filter(id= message_id)
        if message_qs.exists():
            return message_qs.first()

    @database_sync_to_async
    def _get_db_messages(self, start_index, end_index):
        """Retrieves """
        messages = Message.objects.filter(
            conversation= self.conversation
            ).order_by('-sent_at')[start_index:end_index]
        return [message.to_dict() for message in messages]
    
    @database_sync_to_async
    def _messages_list(self, page_number= 1, page_size= 50):
        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size
        
        messages = redis_client.list_messages(self.conversation.id, count=500)

        if start_index < 500:
            paginated_messages = messages[start_index:end_index]
            if end_index > 500:
                db_start_index= 0
                db_end_index = end_index - 500
                db_messages = self._get_db_messages(db_start_index, db_end_index)
                paginated_messages.extend(db_messages)
        else:
            db_start_index = start_index - 500
            db_end_index = end_index - 500
            paginated_messages = self._get_db_messages(db_start_index, db_end_index)
        
        return paginated_messages
    
    @database_sync_to_async
    def _redis_list_messages(conversation_id, count= 500):
        return redis_client.list_messages(conversation_id, count)
    
    @database_sync_to_async
    def _redis_store_message(conversation_id, message):
        print("hereeeee redis 1")
        return redis_client.store_message(conversation_id, message)
    
    @database_sync_to_async
    def _redis_update_message(conversation_id, message_id, data):
        return redis_client.update_message(conversation_id, message_id, data)
    
    @database_sync_to_async
    def _redis_delete_message(conversation_id, message_id):
        return redis_client.delete_message(conversation_id, message_id)
    
    @database_sync_to_async
    def _save_serializer(self, serializer):
        return serializer.save()
