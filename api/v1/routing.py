from django.urls import path

from api.v1.consumers import ConversationConsumer


websocket_urlpatterns= [
    path("ws/conversations/", ConversationConsumer.as_asgi()),
]