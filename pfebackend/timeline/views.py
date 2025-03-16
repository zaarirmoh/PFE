from django.shortcuts import render
from .models import Timeline
from rest_framework.generics import ListAPIView
from .serializers import TimelineSerializer

# Create your views here.
class TimelineListView(ListAPIView):
    queryset = Timeline.objects.all()
    serializer_class = TimelineSerializer
