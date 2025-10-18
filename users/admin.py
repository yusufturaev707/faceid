from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from django.db import models
from django.contrib.postgres.fields import ArrayField
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from unfold.paginator import InfinitePaginator


from users.models import (Role, User, )

class UserLogEntryAdmin(LogEntryAdmin):
    list_display = ['created', 'resource_url', 'action', 'actor', 'msg_short']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['object_repr', 'changes', 'actor__username']

    compressed_fields = True
    warn_unsaved_form = True

    readonly_preprocess_fields = {
        "id": "html.unescape",
        "username": lambda content: content.strip(),
    }
    list_filter_submit = False
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_top = True
    list_disable_select_all = False

    # Custom actions
    actions_list = []  # Displayed above the results list
    actions_row = []  # Displayed in a table row in results list
    actions_detail = []  # Displayed at the top of for in object detail
    actions_submit_line = []  # Displayed near save in object detail

    change_form_show_cancel_button = True

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        }
    }

    paginator = InfinitePaginator
    show_full_result_count = True

# Eski LogEntry admin ni o'chirish va yangisini qo'shish
admin.site.unregister(LogEntry)
admin.site.register(LogEntry, UserLogEntryAdmin)


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'username', 'last_name', 'first_name', 'middle_name', 'telegram_id', 'region', 'role')
    compressed_fields = True
    warn_unsaved_form = True

    readonly_preprocess_fields = {
        "id": "html.unescape",
        "username": lambda content: content.strip(),
    }
    list_filter_submit = False
    list_fullwidth = False
    list_filter_sheet = True
    list_horizontal_scrollbar_top = True
    list_disable_select_all = False

    # Custom actions
    actions_list = []  # Displayed above the results list
    actions_row = []  # Displayed in a table row in results list
    actions_detail = []  # Displayed at the top of for in object detail
    actions_submit_line = []  # Displayed near save in object detail

    change_form_show_cancel_button = True

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
        ArrayField: {
            "widget": ArrayWidget,
        }
    }

    paginator = InfinitePaginator
    show_full_result_count = True


@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = ('id', 'name', 'code', )



admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    list_display = ('id', 'name')