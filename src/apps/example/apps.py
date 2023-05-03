from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DoctorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.example"
    verbose_name = _("Example")
