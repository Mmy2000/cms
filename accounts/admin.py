from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Profile
# Register your models here.

@admin.register(Profile)
class ProfileAdmin(UnfoldModelAdmin):
    list_display = ("user", "syndicate_number", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__first_name", "user__last_name", "syndicate_number")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            'fields': ('user', 'syndicate_number', 'syndicate_card', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    