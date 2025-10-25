from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from django.db import models
from django.contrib.postgres.fields import ArrayField
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from unfold.forms import AdminPasswordChangeForm
from unfold.paginator import InfinitePaginator
from unfold.decorators import display
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from users.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from users.models import (User, Role, )


class UserLogEntryAdmin(LogEntryAdmin, ModelAdmin):
    """Unfold bilan integratsiya qilingan Audit Log."""

    # Asosiy ko'rinish
    list_display = [
        'created',
        'resource_url',
        'action_badge',
        'actor_link',
        'msg_short',
        'content_type_display',
    ]

    list_filter = [
        'action',
        'content_type',
        'timestamp',
        'actor',
    ]

    search_fields = [
        'object_repr',
        'changes',
        'actor__username',
        'actor__email',
        'actor__first_name',
        'actor__last_name',
    ]

    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    # Unfold sozlamalari
    compressed_fields = True
    list_fullwidth = True
    list_filter_sheet = True
    list_horizontal_scrollbar_bottom = True

    # Readonly fields
    readonly_fields = [
        'created',
        'resource_url',
        'action',
        'actor',
        'remote_addr',
        'timestamp',
        'content_type',
        'object_pk',
        'object_repr',
        'changes_display',
        'additional_data_display',
    ]

    # Fieldsets
    fieldsets = (
        ('📊 Asosiy Ma\'lumot', {
            'fields': (
                'timestamp',
                'created',
                'action',
                'actor',
            ),
            'classes': ['tab'],
        }),
        ('🎯 Obyekt', {
            'fields': (
                'content_type',
                'object_pk',
                'object_repr',
                'resource_url',
            ),
            'classes': ['tab'],
        }),
        ('📝 O\'zgarishlar', {
            'fields': (
                'changes_display',
            ),
            'classes': ['tab'],
        }),
        ('💻 Texnik Ma\'lumot', {
            'fields': (
                'remote_addr',
                'additional_data_display',
            ),
            'classes': ['tab', 'collapse'],
        }),
    )

    # Custom display methods
    @display(description='Harakat', label=True)
    def action_badge(self, obj):
        """Harakat badgelari."""
        action_config = {
            0: {'text': 'Yaratildi', 'color': 'success'},
            1: {'text': 'O\'zgartirildi', 'color': 'warning'},
            2: {'text': 'O\'chirildi', 'color': 'danger'},
        }

        config = action_config.get(obj.action, {'text': 'Noma\'lum', 'color': 'info'})
        return config

    @display(description='Foydalanuvchi')
    def actor_link(self, obj):
        """Foydalanuvchi havolasi."""
        if obj.actor:
            url = reverse('admin:users_user_change', args=[obj.actor.pk])
            return format_html(
                '<a href="{}" style="font-weight: 500;">{}</a>',
                url,
                obj.actor.get_full_name() or obj.actor.username
            )
        return '-'

    @display(description='Model')
    def content_type_display(self, obj):
        """Content type nomi."""
        if obj.content_type:
            return f"{obj.content_type.model}".capitalize()
        return '-'

    @display(description='O\'zgarishlar')
    def changes_display(self, obj):
        """O'zgarishlar JSON formati."""
        if obj.changes:
            import json
            try:
                changes = json.loads(obj.changes)
                html = '<div style="font-family: monospace; font-size: 12px;">'
                for field, values in changes.items():
                    old_value = values[0] if len(values) > 0 else 'None'
                    new_value = values[1] if len(values) > 1 else 'None'
                    html += f'''
                        <div style="margin-bottom: 10px; padding: 10px; background: #f3f4f6; border-radius: 6px;">
                            <strong style="color: #1f2937;">{field}:</strong><br>
                            <span style="color: #dc2626;">❌ {old_value}</span><br>
                            <span style="color: #16a34a;">✅ {new_value}</span>
                        </div>
                        '''
                html += '</div>'
                return mark_safe(html)
            except:
                return obj.changes
        return '-'

    @display(description='Qo\'shimcha Ma\'lumot')
    def additional_data_display(self, obj):
        """Qo'shimcha ma'lumotlar."""
        if obj.additional_data:
            import json
            try:
                data = json.loads(obj.additional_data)
                html = '<pre style="background: #f3f4f6; padding: 10px; border-radius: 6px; font-size: 12px;">'
                html += json.dumps(data, indent=2, ensure_ascii=False)
                html += '</pre>'
                return mark_safe(html)
            except:
                return obj.additional_data
        return '-'

    # Permissions
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Eski admin ni o'chirish va yangisini ro'yxatdan o'tkazish
admin.site.unregister(LogEntry)
admin.site.register(LogEntry, UserLogEntryAdmin)



@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

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
    warn_unsaved_form = False
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

        # ========== 1. ADMIN USER ==========
        if user.is_admin or user.is_superuser:
            # Superuser yaratilganda yoki tahrirlanganda Admin guruhiga qo'shish
            if obj.is_superuser:
                try:
                    admin_group = Group.objects.get(name='Admin')
                    # Hali qo'shilmagan bo'lsa qo'shish
                    if not obj.groups.filter(name='Admin').exists():
                        # Avval saqlash kerak (M2M uchun)
                        if not obj.pk:
                            obj.save()
                        obj.groups.add(admin_group)
                        messages.info(
                            request,
                            f"ℹ️ Superuser '{obj.username}' Admin guruhiga avtomatik qo'shildi"
                        )
                except Group.DoesNotExist:
                    messages.warning(
                        request,
                        "⚠️ 'Admin' guruhi topilmadi. 'python manage.py create_groups' kommandasini ishga tushiring"
                    )

            # Oddiy saqlash
            if not change:
                messages.success(request, f"✅ Yangi foydalanuvchi '{obj.username}' yaratildi")
            else:
                messages.success(request, f"✅ Foydalanuvchi '{obj.username}' yangilandi")

            super().save_model(request, obj, form, change)
            return

        # ========== 2. CENTRAL USER ==========
        if user.is_central:
            selected_groups = form.cleaned_data.get('groups', [])

            # Admin yoki Markaz guruhini tekshirish
            forbidden_groups = selected_groups.filter(name__in=['Admin', 'Markaz'])
            if forbidden_groups.exists():
                group_names = ", ".join([g.name for g in forbidden_groups])
                form.add_error(
                    'groups',
                    f'❌ Sizda {group_names} guruhini tayinlash huquqi yo\'q!'
                )
                messages.error(
                    request,
                    f"❌ Sizda '{group_names}' rolini tayinlash huquqi yo'q!",
                    extra_tags='danger'
                )
                return  # Saqlamaslik

            # Superuser yaratishni taqiqlash
            if form.cleaned_data.get('is_superuser', False):
                form.add_error(
                    'is_superuser',
                    '❌ Sizda Superuser yaratish huquqi yo\'q!'
                )
                messages.error(
                    request,
                    "❌ Sizda Superuser yaratish huquqi yo'q!",
                    extra_tags='danger'
                )
                return

            # O'z rolini o'zgartirmasligi
            if change and user == obj:
                # Faqat o'z guruhlarini o'zgartirmoqchi bo'lsa
                original_groups = set(obj.groups.values_list('id', flat=True))
                new_groups = set(selected_groups.values_list('id', flat=True))

                if original_groups != new_groups:
                    form.add_error(
                        'groups',
                        '❌ Siz o\'z rollaringizni o\'zgartira olmaysiz!'
                    )
                    messages.error(
                        request,
                        "❌ Siz o'z rollaringizni o'zgartira olmaysiz!",
                        extra_tags='danger'
                    )
                    return

            if change and user != obj and (obj.is_central or obj.is_admin or obj.is_superuser):
                form.add_error(
                    'groups',
                    "❌ Siz!!"
                )
                messages.error(
                    request,
                    "❌ Sizda huquq yo'q!",
                    extra_tags='danger'
                )
                return

            # Agar barcha tekshiruvdan o'tsa - saqlash
            if not change:
                messages.success(request, f"✅ Yangi foydalanuvchi '{obj.username}' yaratildi")
            else:
                messages.success(request, f"✅ Foydalanuvchi '{obj.username}' yangilandi")

            super().save_model(request, obj, form, change)
            return

        # ========== 3. BOSHQA USERLAR ==========
        messages.error(
            request,
            "❌ Sizda foydalanuvchilarni boshqarish huquqi yo'q!",
            extra_tags='danger'
        )

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass # Agar hali ro'yxatdan o'tmagan bo'lsa

@admin.register(Role)
class RoleAdmin(BaseGroupAdmin, ModelAdmin):
    list_display = ('id', 'name')