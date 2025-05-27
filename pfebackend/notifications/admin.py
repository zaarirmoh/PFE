# from .models import Notification
# from django.contrib import admin



# # admin.site.register(Notification)

from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
)

# Helper function to safely unregister a model if it's registered
def safe_unregister(model):
    if model in admin.site._registry:
        admin.site.unregister(model)

safe_unregister(PeriodicTask)
safe_unregister(IntervalSchedule)
safe_unregister(CrontabSchedule)
safe_unregister(SolarSchedule)
safe_unregister(ClockedSchedule)