# config/admin_config.py
from django.contrib.admin.models import LogEntry
from django.db.models.signals import pre_save, post_save


class AdminLogDisabler:
    """Admin log ni to'liq o'chirish"""

    @staticmethod
    def disable_signals():
        """Signal larni o'chirish"""
        pre_save.disconnect(sender=LogEntry)
        post_save.disconnect(sender=LogEntry)

    @staticmethod
    def disable_save():
        """Save metodini bloklash"""
        LogEntry.save = lambda self, *args, **kwargs: None

    @staticmethod
    def disable_model_admin():
        """ModelAdmin log metodlarini o'chirish"""
        from django.contrib.admin.options import ModelAdmin

        ModelAdmin.log_addition = lambda *args, **kwargs: None
        ModelAdmin.log_change = lambda *args, **kwargs: None
        ModelAdmin.log_deletion = lambda *args, **kwargs: None

    @classmethod
    def disable_all(cls):
        """Hamma usullarni ishga tushirish"""
        cls.disable_signals()
        cls.disable_save()
        cls.disable_model_admin()