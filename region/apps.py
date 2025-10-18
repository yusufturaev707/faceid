from django.apps import AppConfig


class RegionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'region'

    def ready(self):
        from config.admin_config import AdminLogDisabler
        AdminLogDisabler.disable_all()
