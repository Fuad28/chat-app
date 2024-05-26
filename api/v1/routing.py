from django.urls import path

from api.v1.consumers import ConversationConsumer, MessageConsumer, PingPongConsumer


websocket_urlpatterns= [
    path("ws/conversations/", ConversationConsumer.as_asgi()),
    path("ws/conversations/<str:conversation_id>/messages/", MessageConsumer.as_asgi()),
    path("ws/ping/", PingPongConsumer.as_asgi())
]