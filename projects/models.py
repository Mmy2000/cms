from django.db import models
from site_settings.models import validate_svg_or_image
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("Categories")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(_("Project Title"), max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="works",
        verbose_name=_("Project Category"),
    )
    description = models.TextField(_("Description"))
    image = models.ImageField(_("Project Image"), upload_to="work_images/")
    website_logo = models.FileField(
        _("Website Logo"),
        upload_to="website_logo/",
        validators=[validate_svg_or_image],
        null=True,
        blank=True,
    )
    website_url = models.URLField(_("Website Url"), null=True, blank=True)
    priority = models.PositiveIntegerField(
        _("Project Priority"), default=1, null=True, blank=True
    )
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("Our Projects")
        verbose_name_plural = _("Our Projects")

    def __str__(self):
        return self.title
