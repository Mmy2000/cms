from django.db import models
from site_settings.models import validate_svg_or_image
from django.utils.translation import gettext_lazy as _


class About(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"))
    image = models.FileField(
        _("Image"), upload_to="about_images/", validators=[validate_svg_or_image]
    )
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("About")
        verbose_name_plural = _("Abouts")

    def __str__(self):
        return str(self.title)


class Value(models.Model):
    about = models.ForeignKey(
        About, on_delete=models.CASCADE, related_name="values", verbose_name=_("About")
    )
    value = models.CharField(_("Value"), max_length=255)
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("Our Main Concepts")
        verbose_name_plural = _("Our Main Concepts")

    def __str__(self):
        return str(self.value)
