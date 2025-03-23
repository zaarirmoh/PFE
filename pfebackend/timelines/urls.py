from django.urls import path
from .views import *

app_name = 'timeline'

urlpatterns = [
    path('timelines/', TimelineListView.as_view(), name='list'),
    path('timelines/my-timelines/', MyTimelinesView.as_view(), name='my-timelines'),
]