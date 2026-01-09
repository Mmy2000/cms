from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StampsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stamps'
    verbose_name = _('Calculating stamps')

    def ready(self):
        import stamps.signals
