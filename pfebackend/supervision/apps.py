from django.apps import AppConfig


class SupervisionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'supervision'
    
    def ready(self):
        # Import signals to register them
        import supervision.signals
