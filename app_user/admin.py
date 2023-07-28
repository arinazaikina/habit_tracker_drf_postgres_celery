from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Класс, описывающий модель CustomUser в административном интерфейсе.
    """

    model = CustomUser
    list_display = ['pk', 'email', 'first_name', 'last_name', 'tg_id', 'is_active']
    list_display_links = ['pk', 'email']
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'tg_id')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')

    def get_fieldsets(self, request, obj=None):
        """
        Возвращает кортеж кортежей, определяющих расположение полей на форме.
        """
        if not obj:
            fieldsets = (
                (None, {'fields': ('email', 'password1', 'password2')}),
                ('Персональная информация', {'fields': ('first_name', 'last_name', 'tg_id')}),
            )
        else:
            fieldsets = (
                (None, {'fields': ('email',)}),
                ('Персональная информация', {'fields': ('first_name', 'last_name', 'tg_id')}),
                ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
                ('Важные даты', {'fields': ('last_login', 'date_joined')}),
            )
        return fieldsets
