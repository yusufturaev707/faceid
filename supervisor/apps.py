from django.apps import AppConfig


class SupervisorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'supervisor'
    verbose_name = 'BBA'
    verbose_name_plural = 'BBA'

    def ready(self):
        from config.admin_config import AdminLogDisabler
        AdminLogDisabler.disable_all()
