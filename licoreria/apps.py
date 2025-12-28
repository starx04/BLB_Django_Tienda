from django.apps import AppConfig


class LicoreriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'licoreria'

    def ready(self):
        import licoreria.signals
