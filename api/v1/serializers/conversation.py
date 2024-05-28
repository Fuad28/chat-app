from rest_framework import serializers

from api.models import User, Conversation, Message, ConversationMembers, MessageViewers
from api.enums import MessageTypeEnum
from api.v1.serializers import UserRetrieveSerializer


class CreateConversationSerializer(serializers.ModelSerializer):
    """Creates a conversation record"""

    class Meta:
        model= Conversation
        fields= ["id", "name", "created_by",  "is_private"]


    def create(self, validated_data):
        user= self.context.get("request").user
        conversation= Conversation.objects.create(created_by= user, **validated_data)
        conversation.members.add(user)

        convo_member= ConversationMembers.objects.get(
            user= user, 
            conversation= conversation
        )
        convo_member.is_admin= True
        convo_member.save()

        return conversation

class SimpleConversationSerializer(serializers.ModelSerializer):   
    number_of_unreads= serializers.SerializerMethodField()

    class Meta:
        model= Conversation
        fields= ["id", "name",  "is_private", "number_of_unreads"]

    
    def get_number_of_unreads(self, instance: Conversation):
        user= self.context.get("request").user

        try:
            joined_at = ConversationMembers.objects.get(
                user= user, conversation= instance).joined_at
        except ConversationMembers.DoesNotExist:
            return 0

        return Message.objects.filter(
            conversation= instance, 
            sent_at__gte= joined_at
            ).exclude(
                seen_by=user
            ).count()

class ConversationSerializer(serializers.ModelSerializer):
    created_by= UserRetrieveSerializer()
    members= UserRetrieveSerializer(many= True)
   

    class Meta:
        model= Conversation
        fields= [
            "id", "name", "created_by", "created_at",
            "updated_at", "is_private", "members"
        ]

class AddORemoveMemberConversationSerializer(serializers.Serializer):
    user= serializers.PrimaryKeyRelatedField(queryset= User.objects.all())
    

class MarkMessageReadSerializer(serializers.Serializer):
    message= serializers.PrimaryKeyRelatedField(queryset= Message.objects.all())
    seen_at= serializers.DateTimeField()

    def create(self, validated_data):
        user= self.context.get("user")
        return MessageViewers.objects.create(user= user, **validated_data)
    

class SimpleMessageSerializer(serializers.ModelSerializer):
    sent_by= UserRetrieveSerializer()
    is_mine= serializers.SerializerMethodField()
    class Meta:
        model= Message
        fields= [
            "id","conversation", "message_type", "media_url", "text",
            "is_mine", "sent_at", "updated_at", "deleted_at", "sent_by",  "seen_by",
        ]

    def get_is_mine(self, instance: Message):
        return self.context.get("user") == instance.sent_by
    

    def to_representation(self, instance: Message):
        data= super().to_representation(instance)

        if instance.deleted_at:
            data["text"]= ""
            data["media_url"]= ""
        
        return data
    
        
class MessageSerializer(SimpleMessageSerializer):
    seen_by= UserRetrieveSerializer(many= True)


class CreateMessageSerializer(serializers.ModelSerializer):
    """Creates a message record"""
    
    class Meta:
        model= Message
        fields= ["id", "media_url",  "text", "message_type"]
    
    def validate(self, attrs):
        message_type= attrs.get('message_type')
        media_url= attrs.get('media_url')
        text= attrs.get('text')

        if (message_type == MessageTypeEnum.TEXT) and (not text):
            raise serializers.ValidationError(
                "Message of type text must contain a text.")

        if (message_type != MessageTypeEnum.TEXT) and (not media_url):
            raise serializers.ValidationError(
                "Message of types audio, video and image contain a media_url.")
        
        if text and media_url:
            raise serializers.ValidationError(
                "Messages can only be a single type.")

        
        return attrs
    
    def to_representation(self, instance):
        return SimpleMessageSerializer(instance= instance).data
    

    def create(self, validated_data):
        user= self.context.get("user")
        conversation_id= self.context.get("conversation_id")

        message= Message.objects.create(
            sent_by= user, 
            conversation_id= conversation_id, 
            **validated_data
        )
        message.seen_by.add(user)

        return message


class UpdateMessageSerializer(serializers.ModelSerializer):
    """Updates a message record"""
    class Meta:
        model= Message
        fields= ["id", "media_url",  "text"]
    
    def validate(self, attrs):
        message_type = self.context.get("message_type")
        media_url= attrs.get('media_url')
        text= attrs.get('text')

        if (message_type == MessageTypeEnum.TEXT) and media_url:
            raise serializers.ValidationError(
                "Message of type text must only contain text.")
        
        if (message_type != MessageTypeEnum.TEXT) and text:
            raise serializers.ValidationError(
                "Message of types audio, video and image only contain media_url.")
        
        return attrs
    
    def to_representation(self, instance):
        return SimpleMessageSerializer(instance= instance).data
