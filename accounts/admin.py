from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

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


# User Admin

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, UnfoldModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, UnfoldModelAdmin):
    pass
