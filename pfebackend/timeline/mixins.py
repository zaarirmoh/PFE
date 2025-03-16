from rest_framework.exceptions import PermissionDenied
import logging
from .models import Timeline

logger = logging.getLogger(__name__)

class APITimelineRequiredMixin:
    """
    API version of TimelineRequiredMixin for use with JWT authenticated DRF views.
    
    This mixin checks if at least one of the specified timelines is current.
    
    Usage:
        # For a single timeline:
        class MySingleTimelineView(APITimelineRequiredMixin, ListCreateAPIView):
            timeline_slugs = Timeline.GROUPS
            
        # For multiple timelines:
        class MyMultiTimelineView(APITimelineRequiredMixin, ListCreateAPIView):
            timeline_slugs = [Timeline.GROUPS, Timeline.THEMES]
    """
    timeline_slugs = None  # Can be a single timeline slug or a list of timeline slugs
    
    def initial(self, request, *args, **kwargs):
        """
        Check timeline requirements before processing the request.
        """
        # Call parent initial method
        super().initial(request, *args, **kwargs)
        
        # Get the timeline slugs from the class attribute
        timeline_slugs = self.timeline_slugs
        
        # Convert single string to list for consistent handling
        if isinstance(timeline_slugs, str):
            timeline_slugs = [timeline_slugs]
        
        logger.debug(f"Timeline slugs: {timeline_slugs}")
        
        # Check if any timelines are specified
        if not timeline_slugs:
            self.handle_no_permission("No timelines specified for this resource.")
        
        # Try to find at least one valid and current timeline
        valid_timelines = []
        for slug in timeline_slugs:
            try:
                timeline = Timeline.objects.get(slug=slug)
                if timeline.is_active and timeline.is_current:
                    valid_timelines.append(timeline)
            except Timeline.DoesNotExist:
                logger.warning(f"Timeline '{slug}' does not exist.")
                continue
        
        # If no valid timelines were found, explain why
        if not valid_timelines:
            # Get status info for all timelines to provide better error messages
            timelines_info = []
            for slug in timeline_slugs:
                try:
                    timeline = Timeline.objects.get(slug=slug)
                    if not timeline.is_active:
                        timelines_info.append(f"'{timeline.name}' is not active")
                    elif timeline.status == 'upcoming':
                        timelines_info.append(f"'{timeline.name}' has not started yet (starts on {timeline.start_date.strftime('%Y-%m-%d %H:%M')})")
                    elif timeline.status == 'expired':
                        timelines_info.append(f"'{timeline.name}' has ended (ended on {timeline.end_date.strftime('%Y-%m-%d %H:%M')})")
                    else:
                        timelines_info.append(f"'{timeline.name}' is not current")
                except Timeline.DoesNotExist:
                    timelines_info.append(f"'{slug}' does not exist")
            
            if timelines_info:
                detail = "None of the specified timelines are available: " + "; ".join(timelines_info)
            else:
                detail = "No valid timelines available for this resource."
                
            self.handle_no_permission(detail)
        
        # Store the first valid timeline for use in the view
        # (views can access all valid timelines through the _valid_timelines attribute if needed)
        request.current_timeline = valid_timelines[0]
        request._valid_timelines = valid_timelines
    
    def handle_no_permission(self, message=None):
        """Raise appropriate DRF exception with message."""
        detail = message if message else "Timeline requirement not met."
        raise PermissionDenied(detail=detail)
    
