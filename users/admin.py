from django.contrib import admin

from users.models import User, Role


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'last_name', 'first_name', 'middle_name', 'telegram_id', 'zone', 'role')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', )