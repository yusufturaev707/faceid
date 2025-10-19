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
from users.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.core.exceptions import ValidationError
from users.models import (User, )

class UserLogEntryAdmin(LogEntryAdmin):
    list_display = ['created', 'resource_url', 'action', 'actor', 'msg_short']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['object_repr', 'changes', 'actor__username']


# Eski LogEntry admin ni o'chirish va yangisini qo'shish
admin.site.unregister(LogEntry)
admin.site.register(LogEntry, UserLogEntryAdmin)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('id', 'username', 'last_name', 'first_name', 'middle_name', 'display_groups', 'region')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name',)
    readonly_fields = ('last_login',)
    filter_horizontal = ('groups',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'middle_name', 'region'),
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff'),
        }),
    )

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'middle_name', 'region', 'telegram_id')
        }),
        ('Rollar', {
            'fields': ('groups',)
        }),
        ('Huquqlar va status', {
            'fields': ('is_active', 'is_staff')
        }),
        ('Muhim sanalar', {
            'fields': ('last_login',),
        }),
        ('Face Rasm', {
            'fields': ('img_b64', 'img_vector')
        }),
    )

    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = False
    list_fullwidth = False
    list_filter_sheet = False
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

    def display_groups(self, obj):
        """Guruhlarni chiroyli ko'rsatish"""
        groups = obj.groups.all()
        if groups:
            return ", ".join([g.name for g in groups])
        return "-"

    display_groups.short_description = 'Rollar'

    def get_form(self, request, obj=None, **kwargs):
        """user_permissions maydonini formadan olib tashlash"""
        form = super().get_form(request, obj, **kwargs)
        if 'user_permissions' in form.base_fields:
            del form.base_fields['user_permissions']
        return form

    def save_model(self, request, obj, form, change):
        user = request.user
        if user.is_admin:
            if not change:
                messages.success(request, f"✅ Yangi user '{obj.username}' yaratildi")
            else:
                messages.success(request, f"✅ User '{obj.username}' yangilandi")

            super().save_model(request, obj, form, change)
            return

        if user.is_central:
            if not change:
                messages.success(request, f"✅ Yangi user '{obj.username}' yaratildi")
                super().save_model(request, obj, form, change)
                return
            selected_groups = form.cleaned_data.get('groups', [])

            # Admin guruhini tekshirish
            if selected_groups.filter(name='Admin').exists() or selected_groups.filter(name='Markaz').exists():
                form.add_error(
                    'groups',
                    '❌ Sizda Admin guruhini tayinlash huquqi yo\'q!'
                )
                messages.error(
                    request,
                    "❌ Sizda Admin va Markaz rolini tayinlash huquqi yo'q!", extra_tags='danger'
                )
                return
            else:
                super().save_model(request, obj, form, change)
                return

        # 3. Boshqa userlar - huquq yo'q
        messages.error(
            request,
            "❌ Sizda foydalanuvchilarni boshqarish huquqi yo'q!"
        )
        raise ValidationError("Foydalanuvchilarni boshqarish huquqi yo'q", code='permission_denied')

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    list_display = ('id', 'name')