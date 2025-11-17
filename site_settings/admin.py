from django.contrib import admin
from .models import SiteConfiguration
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.utils.html import format_html

# Register your models here.

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(UnfoldModelAdmin):
    list_display = ("preview_logo","site_name")
    search_fields = ("copyright_info", "about_site")
    ordering = ("-id",)
    fieldsets = (
        (None, {"fields": ("site_name","site_logo", "about_site", "copyright_info")}),
        ("Social Links", {"fields": ("instagram_link", "facebook_link", "linkedIn_link")}),
    )

    def preview_logo(self, obj):
        if obj.site_logo:
            return format_html(
                '<img src="{}" style="height:40px; border-radius:6px;">',
                obj.site_logo.url,
            )
        return "—"

    preview_logo.short_description = "Logo"
