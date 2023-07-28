from django.contrib import admin

from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user', 'action', 'place', 'time', 'periodicity']
    list_display_link = ['action']
