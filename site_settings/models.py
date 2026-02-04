from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import os

# Create your models here.


def validate_svg_or_image(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg"]

    if ext not in allowed_extensions:
        raise ValidationError("Only JPG, PNG, GIF, and SVG files are allowed.")


class SiteConfiguration(models.Model):
    site_logo = models.ImageField(_("Site Logo"),upload_to='site_logos/', blank=True, null=True)
    site_name = models.CharField(_("Site Name"),max_length=255, blank=True, null=True)
    about_site = models.TextField(_("About Site"),blank=True, null=True)
    number_of_retired_engineers = models.PositiveIntegerField(_("Number of Retired Engineers"),default=0)
    current_pension = models.DecimalField(_("Current Pension"),max_digits=10, decimal_places=2, default=0.00)
    pension_description = models.TextField(_("Pension Description"),blank=True, null=True)
    copyright_info = models.CharField(_("Copyright Info"),max_length=255, blank=True, null=True)
    instagram_link = models.URLField(_("Instagram Link"),max_length=200, blank=True, null=True)
    facebook_link = models.URLField(_("Facebook Link"),max_length=200, blank=True, null=True)
    linkedIn_link = models.URLField(_("LinkedIn Link"),max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = _("Site Configuration")
        verbose_name_plural = _("Site Configurations")

    def __str__(self):
        return str(self.id)


class Page(models.Model):
    page_name = models.CharField(_("Page Name"),max_length=255)
    page_url = models.CharField(_("Page URL"),max_length=255, unique=True)
    active = models.BooleanField(_("Active") , default=True)

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")

    def __str__(self):
        return self.page_name

class SEOSettings(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='seo_settings', verbose_name=_("Page"))
    meta_title = models.CharField(_("Meta Title"),max_length=255, blank=True, null=True)
    meta_keywords = models.TextField(_("Meta Keywords"),blank=True, null=True)
    meta_description = models.TextField(_("Meta Description"),blank=True, null=True)

    class Meta:
        verbose_name = _("SEO Setting")
        verbose_name_plural = _("SEO Settings")

    def __str__(self):
        return str(self.id)


class AdminAllowedIP(models.Model):
    ip_address = models.GenericIPAddressField(_("IP Address"),unique=True)
    description = models.CharField(_("IP Address Description"),max_length=255, blank=True)
    active = models.BooleanField(_("Active"),default=True)
    created_at = models.DateTimeField(_("created_at"),auto_now_add=True)

    class Meta:
        verbose_name = _("Allowed Admin IP")
        verbose_name_plural = _("Allowed Admin IPs")

    def __str__(self):
        return f"{self.ip_address}"
