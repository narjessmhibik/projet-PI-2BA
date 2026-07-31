from django.apps import AppConfig

class FlowerDetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flower_detector'


class FlowerDetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flower_detector'

    def ready(self):
        import flower_detector.signals  # Importer les signals