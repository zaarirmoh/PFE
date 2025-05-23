import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pfebackend.settings.dev')

app = Celery('pfebackend')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Fix for broker_connection_retry warning
app.conf.broker_connection_retry_on_startup = True

# Explicitly discover tasks from all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
