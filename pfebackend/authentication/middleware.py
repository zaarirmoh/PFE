from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from asgiref.sync import sync_to_async



from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
<<<<<<< HEAD
        # Initialize user as AnonymousUser by default
        scope["user"] = AnonymousUser()
        
        # Try to get token from headers first
        headers = dict(scope["headers"])
        auth_header = headers.get(b"authorization", b"").decode("utf-8")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            authenticated = await self.authenticate_token(token, scope)
            if authenticated:
                return await super().__call__(scope, receive, send)
        
        # If no valid token in headers, try query parameters
        if scope["type"] == "websocket":
            # Parse query string
            query_string = scope.get("query_string", b"").decode("utf-8")
            if query_string:
                query_params = parse_qs(query_string)
                token = query_params.get("token", [""])[0]
                if token:
                    await self.authenticate_token(token, scope)
        
        return await super().__call__(scope, receive, send)
    
    async def authenticate_token(self, token, scope):
        """Authenticate a token and set user in scope if valid"""
        try:
            # Validate JWT token
            jwt_authentication = JWTAuthentication()
            validated_token = jwt_authentication.get_validated_token(token)
            user = await sync_to_async(jwt_authentication.get_user)(validated_token)
            scope["user"] = user
            return True
        except (InvalidToken, AuthenticationFailed):
            return False
=======
        query_string = scope.get("query_string", b"").decode("utf-8")
        token = dict(x.split("=") for x in query_string.split("&")).get("token", "")

        if token:
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                scope["user"] = await sync_to_async(jwt_auth.get_user)(validated_token)
            except (InvalidToken, AuthenticationFailed):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
>>>>>>> 31b87d668c17172675f33146da4a0c4846a12264
