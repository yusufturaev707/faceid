from django.apps import AppConfig


class AccessControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'access_control'
    verbose_name = 'Kirish boshqaruvi'
    verbose_name_plural = 'Kirish boshqaruvlari'

    def ready(self):
        from config.admin_config import AdminLogDisabler
        AdminLogDisabler.disable_all()
