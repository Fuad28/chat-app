from django.conf import settings

import redis
import json

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db)
    
    def store_message(self, conversation_id, message) -> None:
        key = f"conversation:{conversation_id}:messages"
        self.client.rpush(key, json.dumps(message))
        self.client.ltrim(key, -500, -1)
    
    def delete_message(self, conversation_id, message_id) -> None:
        key = f"conversation:{conversation_id}:messages"

        messages = self.client.lrange(key, 0, -1)
        for msg in messages:
            message = json.loads(msg)
            if message['id'] == message_id:
                self.client.lrem(key, 1, msg)
                break
    
    def get_message(self, conversation_id, message_id):
        key = f"conversation:{conversation_id}:messages"

        messages = self.client.lrange(key, 0, -1)
        for msg in messages:
            message = json.loads(msg)
            if message['id'] == message_id:
                return message
            
        return None
    

    def update_message(self, conversation_id, message_id, data):
        key = f"conversation:{conversation_id}:messages"
        messages = self.client.lrange(key, 0, -1)

        for idx, msg in enumerate(messages):
            message = json.loads(msg)
            if message['id'] == message_id:
                message.update(data)
                self.client.lset(key, idx, json.dumps(message))
                break
    
    def get_recent_messages(self, conversation_id, count=500):
        key = f"conversation:{conversation_id}:messages"
        recent_messages = self.client.lrange(key, -count, -1)
        return [json.loads(msg) for msg in recent_messages]
    




redis_client = RedisClient(settings.REDIS_HOST, settings.REDIS_PORT)