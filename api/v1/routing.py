from django.urls import re_path

from api.v1.consumers import ConversationConsumer, MessageConsumer, PingPongConsumer


websocket_urlpatterns= [
    re_path("ws/conversations/", ConversationConsumer.as_asgi()),
    re_path("ws/conversations/<str:conversation_id>/messages", MessageConsumer.as_asgi()),
    re_path("ws/ping/", PingPongConsumer.as_asgi())
]