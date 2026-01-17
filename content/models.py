from django.db import models
from django.utils.translation import gettext_lazy as _


class Content(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcontents",
        verbose_name=_("Parent Content"),
    )

    image = models.ImageField(
        _("Image"), upload_to="content_images/", null=True, blank=True
    )


    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = _("Content")
        verbose_name_plural = _("Contents")

    def __str__(self):
        return self.title

    def is_main_topic(self):
        return self.parent is None


class ContentImage(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Content"),
    )
    image = models.ImageField(_("Image"), upload_to="content_images/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Content Image")
        verbose_name_plural = _("Content Images")

    def __str__(self):
        return f"{self.content.title} - Image"

class ContentFile(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name=_("Content"),
    )
    file = models.FileField(_("File"), upload_to="content_files/")
    description = models.TextField(_("Description"), blank=True,null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Content File")
        verbose_name_plural = _("Content Files")

    def __str__(self):
        return f"{self.content.title} - File"
