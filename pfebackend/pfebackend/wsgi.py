"""
WSGI config for pfebackend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from pfebackend.settings import base

if base.DEBUG:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfebackend.settings.dev')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfebackend.settings.prod')

application = get_wsgi_application()
