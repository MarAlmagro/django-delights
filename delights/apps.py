from django.apps import AppConfig


class DelightsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "delights"

    def ready(self):
        import delights.signals  # noqa: F401
