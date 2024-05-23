from rest_framework import serializers

from api.models import User, Conversation, Message, ConversationMembers
from api.enums import MessageTypeEnum
from api.v1.serializers import UserRetrieveSerializer


class CreateConversationSerializer(serializers.ModelSerializer):
    """Creates a conversation record"""

    class Meta:
        model= Conversation
        fields= ["id", "name", "created_by",  "is_private"]


    def create(self, validated_data):
        user= self.context.get("request").user
        conversation= Conversation.objects.create(user= user, **validated_data)
        conversation.members.add(user)


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
    

class CreateMessageSerializer(serializers.ModelSerializer):
    """Creates a message record"""

    class Meta:
        model= Conversation
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


    def create(self, validated_data):
        #TODO: REMEMBER TO UPDATE IS_SENT IN WS

        user= self.context.get("request").user
        conversation_id= self.context.get("conversation_pk")
        message= Message.objects.create(
            sent_by= user, 
            conversation_id= conversation_id, 
            **validated_data
        )
        message.seen_by.add(user)

        return message
    


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model= Conversation
        fields= [
            "id", "conversation", "sent_by",  "sent_at",
            "seen_by", "updated_at", "media_url", "text", "message_type"
        ]