from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from config.admin_config import AdminLogDisabler
        AdminLogDisabler.disable_all()
