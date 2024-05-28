from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from api.models import Message
from api.v1.utils import update_conversation_cache, broadcast_conversation_event
from api.v1.signals import new_conversation_event
from api.v1.serializers.conversation import SimpleMessageSerializer


@receiver(post_save, sender= Message)
def handle_saved_message(sender, **kwargs):
        message: Message= kwargs["instance"]
        update_conversation_cache(message.conversation.id, 500)

        if kwargs["created"]:
                broadcast_conversation_event(
                        message.conversation.id,
                        {
                                "type": "new.message",
                                "message": SimpleMessageSerializer(message).data
                        })



@receiver(post_delete, sender= Message)
def handle_deleted_message(sender, **kwargs):
        message: Message= kwargs["instance"]
        update_conversation_cache(message.conversation.id, 500)



@receiver(new_conversation_event)
def handle_new_conversation_event(sender, **kwargs):
        broadcast_conversation_event(
                kwargs["conversation_id"],
                kwargs["event"]
        )