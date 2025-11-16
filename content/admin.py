from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from django.utils.translation import gettext_lazy as _
from .models import Content, ContentImage, ContentFile
from unfold.admin import StackedInline, TabularInline


# ------------------------------
# Inline image uploader with preview
# ------------------------------
class ContentImageInline(TabularInline):
    model = ContentImage
    extra = 1
    fields = ("image", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" style="border-radius:6px;"/>', obj.image.url
            )
        return "—"

    image_preview.short_description = "Preview"


# ------------------------------
# Inline file uploader with size & description
# ------------------------------
class ContentFileInline( TabularInline):
    model = ContentFile
    extra = 1
    fields = ("file", "description", "uploaded_at")
    readonly_fields = ("uploaded_at",)


# ------------------------------
# Main Content Admin
# ------------------------------
@admin.register(Content)
class ContentAdmin(UnfoldModelAdmin):
    list_display = ("title", "parent", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("created_at", "updated_at", "parent")
    ordering = ("title",)
    autocomplete_fields = ("parent",)

    fieldsets = (
        (_("Basic Information"), {"fields": ("title", "description", "parent")}),
        (
            _("Main Image"),
            {"fields": ("image",), "classes": ("collapse",)},  # collapsible section
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    inlines = [ContentImageInline, ContentFileInline]


@admin.register(ContentImage)
class ContentImageAdmin(UnfoldModelAdmin):
    list_display = ("content", "image", "uploaded_at")
    search_fields = ("content__title",)
    list_filter = ("uploaded_at",)
    ordering = ("-uploaded_at",)


@admin.register(ContentFile)
class ContentFileAdmin(UnfoldModelAdmin):
    list_display = ("content", "file", "description", "uploaded_at")
    search_fields = ("content__title", "description")
    list_filter = ("uploaded_at",)
    ordering = ("-uploaded_at",)
