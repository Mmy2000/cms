from django.db.models.signals import pre_save
from django.dispatch import receiver

from stamps.tasks import send_email
from .models import Profile


@receiver(pre_save, sender=Profile)
def send_email_on_approval(sender, instance, **kwargs):
    if not instance.pk:
        return  # new profile

    previous = sender.objects.get(pk=instance.pk)
    if previous.status != "approved" and instance.status == "approved":
        subject = "Your account is approved!"
        message = f"Hi {instance.user.first_name},\n\nYour account has been approved. You can now log in."
        send_email.enqueue(
            to_email=instance.user.email,
            first_name=instance.user.first_name,
            subject=subject,
            message=message,
        )
        
