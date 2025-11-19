from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class SiteConfiguration(models.Model):
    site_logo = models.ImageField(_("Site Logo"),upload_to='site_logos/', blank=True, null=True)
    site_name = models.CharField(_("Site Name"),max_length=255, blank=True, null=True)
    about_site = models.TextField(_("About Site"),blank=True, null=True)
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