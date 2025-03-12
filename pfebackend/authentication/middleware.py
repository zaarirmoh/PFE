from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from asgiref.sync import sync_to_async

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract JWT token from headers
        headers = dict(scope["headers"])
        auth_header = headers.get(b"authorization", b"").decode("utf-8")

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Validate JWT token
                jwt_authentication = JWTAuthentication()
                validated_token = jwt_authentication.get_validated_token(token)
                user = await sync_to_async(jwt_authentication.get_user)(validated_token)
                scope["user"] = user
            except (InvalidToken, AuthenticationFailed):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)