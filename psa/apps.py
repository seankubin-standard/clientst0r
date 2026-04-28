from django.apps import AppConfig


class PsaConfig(AppConfig):
    name = 'psa'
    verbose_name = 'Native PSA / Service Desk'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import signals  # noqa: F401
