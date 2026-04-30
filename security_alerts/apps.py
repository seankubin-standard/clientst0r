from django.apps import AppConfig


class SecurityAlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security_alerts'
    verbose_name = 'Security Alerts'

    def ready(self):
        # Auto-register all bundled vendor adapters so the registry is
        # populated by the time `poll_security_alerts` or the webhook
        # receiver looks up a slug.
        try:
            from . import adapters  # noqa: F401
        except Exception:
            # Don't crash app startup if a third-party SDK is missing —
            # adapters are best-effort optional plug-ins.
            import logging
            logging.getLogger('security_alerts').exception(
                'failed to autoload security_alerts.adapters package'
            )
