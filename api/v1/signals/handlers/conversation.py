from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from api.models import Message
from api.v1.utils import update_conversation_cache
from api.v1.serializers.conversation import SimpleMessageSerializer

@receiver(post_save, sender= Message)
def handle_saved_message(sender, **kwargs):
        message: Message= kwargs["instance"]
        update_conversation_cache(message.conversation.id, 500)

        if kwargs["created"]:
                group_name= str(message.conversation.id)
                message= SimpleMessageSerializer(message).data

                async_to_sync(get_channel_layer().group_send)(
                group_name, 
                {"type": "send.message", "message": message}
        )



@receiver(post_delete, sender= Message)
def handle_deleted_message(sender, **kwargs):
        message: Message= kwargs["instance"]
        update_conversation_cache(message.conversation.id, 500)