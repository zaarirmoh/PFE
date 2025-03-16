from django.apps import AppConfig


class TimelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timeline'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        """
        # Import the models here to avoid circular imports
        from django.core import management
        
        # Only run in non-testing environments
        import sys
        if 'runserver' in sys.argv or 'runserver_plus' in sys.argv:
            # Use a slight delay to ensure DB is ready
            from threading import Timer
            Timer(1, lambda: management.call_command('create_timelines')).start()
