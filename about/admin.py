from django.contrib import admin
from unfold.admin import ModelAdmin,TabularInline
from django.utils.html import format_html
from .models import About, Value


class ValueInline(TabularInline):
    model = Value
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(About)
class AboutAdmin(ModelAdmin):
    list_display = (
        "title",
        "preview_image",
        "created_at",
    )

    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at", "preview_image")
    inlines = (ValueInline,)

    fieldsets = (
        (
            "Main Information",
            {
                "fields": ("title", "description"),
            },
        ),
        (
            "Media",
            {
                "fields": ("image", "preview_image"),
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
                '<img src="{}" style="width:140px;height:auto;border-radius:10px;" />',
                obj.image.url,
            )
        return "—"

    preview_image.short_description = "Preview"


@admin.register(Value)
class ValueAdmin(ModelAdmin):
    list_display = (
        "value",
        "about",
        "created_at",
    )

    search_fields = ("value",)
    list_filter = ("about",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    autocomplete_fields = ("about",)

    fieldsets = (
        (
            "Concept Details",
            {
                "fields": ("about", "value"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
