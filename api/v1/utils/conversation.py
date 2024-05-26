from django.core.cache import cache

from api.models import Message

def update_conversation_cache(conversation_id, count):
	cache_key = f"messages:conversation:{conversation_id}"
	cached_messages = list(
		Message.objects.filter(
			conversation_id= conversation_id
			).order_by('-sent_at')[:count]
		)
			
	cache.set(cache_key, cached_messages, timeout= 60*60*24)

	return cached_messages