from django.apps import AppConfig


class ExamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exam'

    def ready(self):
        from config.admin_config import AdminLogDisabler
        AdminLogDisabler.disable_all()