from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Content

# ------------------------------
# User & Group Admin using Unfold
# ------------------------------
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, UnfoldModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, UnfoldModelAdmin):
    pass


# ------------------------------
# Content Admin
# ------------------------------

@admin.register(Content)
class ContentAdmin(UnfoldModelAdmin):
    list_display = ("title", "slug", "parent", "created_at", "updated_at")
    search_fields = ("title", "slug", "description")
    list_filter = ("created_at", "updated_at", "parent")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("title",)
    fieldsets = (
        (None, {"fields": ("title", "slug", "description", "parent")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("parent",)
