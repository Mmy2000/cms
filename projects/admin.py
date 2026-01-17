from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import Category, Project


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Category Information", {"fields": ("name",)}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = (
        "title",
        "category",
        "priority",
        "preview_image",
        "website_link",
        "created_at",
    )

    list_filter = ("category",)
    search_fields = ("title", "description")
    ordering = ("priority", "-created_at")
    readonly_fields = ("created_at", "updated_at", "preview_image")

    autocomplete_fields = ("category",)

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("title", "category", "priority"),
            },
        ),
        (
            "Content",
            {
                "fields": ("description", "image", "preview_image"),
            },
        ),
        (
            "Website Info",
            {
                "fields": ("website_logo", "website_url"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:120px;height:auto;border-radius:8px;" />',
                obj.image.url,
            )
        return "—"

    preview_image.short_description = "Preview"

    def website_link(self, obj):
        if obj.website_url:
            return format_html(
                '<a href="{}" target="_blank">Visit</a>',
                obj.website_url,
            )
        return "—"

    website_link.short_description = "Website"
