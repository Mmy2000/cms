from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile",verbose_name=_("User")
    )
    syndicate_number = models.CharField(max_length=50, unique=True, verbose_name=_("Syndicate Number"),error_messages={
        'unique': _("Profile with this Syndicate Number already exists."),
    },)
    syndicate_card = models.ImageField(upload_to="syndicate_cards/", verbose_name=_("Syndicate Card"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name=_("Status"))
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
