from django.contrib import admin
from .models import SiteConfiguration, Page, SEOSettings
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.utils.html import format_html

# Register your models here.

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(UnfoldModelAdmin):
    list_display = ("preview_logo","site_name", "number_of_retired_engineers", "current_pension")
    search_fields = ("copyright_info", "about_site")
    ordering = ("-id",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "site_name",
                    "site_logo",
                    "about_site",
                    "copyright_info",
                    "number_of_retired_engineers",
                    "current_pension",
                    "pension_description",
                )
            },
        ),
        (
            "Social Links",
            {"fields": ("instagram_link", "facebook_link", "linkedIn_link")},
        ),
    )

    def preview_logo(self, obj):
        if obj.site_logo:
            return format_html(
                '<img src="{}" style="height:40px; border-radius:6px;">',
                obj.site_logo.url,
            )
        return "—"

    preview_logo.short_description = "Logo"

@admin.register(Page)
class PageAdmin(UnfoldModelAdmin):
    list_display = ("page_name", "page_url","active")
    search_fields = ("page_name", "page_url")
    ordering = ("page_name",)
    fieldsets = (
        (None, {"fields": ("page_name", "page_url","active")}),
    )

@admin.register(SEOSettings)
class SEOSettingsAdmin(UnfoldModelAdmin):
    list_display = ("page", "meta_title")
    search_fields = ("meta_title", "meta_keywords", "meta_description")
    ordering = ("-id",)
    fieldsets = (
        (None, {"fields": ("page", "meta_title", "meta_keywords", "meta_description")}),
    )
