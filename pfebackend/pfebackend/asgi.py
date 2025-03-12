"""
ASGI config for pfebackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
import notifications.routing
from pfebackend.settings import base
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from notifications.routing import websocket_urlpatterns as notifications_websocket_urlpatterns
from authentication.middleware import JWTAuthMiddleware

if base.DEBUG:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfebackend.settings.dev')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfebackend.settings.prod')
    

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(
                URLRouter(
                    chat_websocket_urlpatterns +
                    notifications_websocket_urlpatterns,
                    )
                )
        ),
})