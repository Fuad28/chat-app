from django.db import models
from django.core.cache import cache

class CachedMessageQuerySet(models.QuerySet):
	
	def get_messages(self, conversation_id, offset, limit, count= 500):
		start_index = offset
		end_index = offset + limit

		cache_key = f"messages:conversation:{conversation_id}"
		cached_messages = cache.get(cache_key)

		if cached_messages is None:
			cache_key = f"messages:conversation:{conversation_id}"
			cached_messages = list(
				self.model.objects.filter(
					conversation_id= conversation_id
					).order_by('-sent_at')[:count]
				)
			
			cache.set(cache_key, cached_messages, timeout= 60*60*24)

		if (end_index > count) and (len(cached_messages) == count):
			db_start_index = max(0, start_index - count)
			db_end_index = end_index - count
			db_messages = list(
				self.model.objects.filter(
					conversation_id=conversation_id
				).order_by('-sent_at')[db_start_index:db_end_index]
			)
			messages = cached_messages + db_messages
		else:
			messages = cached_messages[start_index:end_index]

		return messages