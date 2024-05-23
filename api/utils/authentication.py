from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
from urllib.parse import parse_qs


class JWTAuthMiddleware(BaseMiddleware):
    """Websocket authentication middleware. """

    def __init__(self, inner):
        super().__init__(inner)
        self.authenticator = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        try:
            scope["user"] = await self.authenticate(scope)
            return await super().__call__(scope, receive, send)

        except Exception:
            return await send({
                "type": "websocket.close",
                "close": True,
                "message": "Invalid credentials",
                "code": 4401,  # Custom close code for authentication failure
            })

    @database_sync_to_async
    def authenticate(self, scope):
        token = parse_qs(scope["query_string"].decode("utf8")).get("token")[0]
        validated_token = self.authenticator.get_validated_token(token)

        return self.authenticator.get_user(validated_token)