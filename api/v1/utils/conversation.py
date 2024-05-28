from django.core.cache import cache

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from api.models import Message

def update_conversation_cache(conversation_id, count):
	"""
	Updates the cache with the most recent `count` messages in the conversation.
	Usuall called after database operations on  a conversation.
	"""

	cache_key = f"messages:conversation:{conversation_id}"
	cached_messages = list(
		Message.objects.filter(
			conversation_id= conversation_id
			).order_by('-sent_at')[:count]
		)
			
	cache.set(cache_key, cached_messages, timeout= 60*60*24)

	return cached_messages



def broadcast_conversation_event(conversation_id, event):
	"""
	Broadcast events from the application to the channels.

	'event' should contain only type and message key.
	"""

	group_name= str(conversation_id)
	
	async_to_sync(get_channel_layer().group_send)(
		group_name, 
		{"type": "send.message", "message": event}
)
