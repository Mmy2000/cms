from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Profile
from .tasks import send_email


@receiver(pre_save, sender=Profile)
def send_email_on_approval(sender, instance, **kwargs):
    if not instance.pk:
        return  # new profile

    previous = sender.objects.get(pk=instance.pk)
    if previous.status != "approved" and instance.status == "approved":
        subject = "Your account is approved!"
        message = f"Hi {instance.user.first_name},\n\nYour account has been approved. You can now log in."
        send_email.delay(
            instance.user.email, instance.user.first_name, subject, message
        )
