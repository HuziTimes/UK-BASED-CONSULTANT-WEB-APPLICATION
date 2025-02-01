from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User  # Import your User model
from .utils import send_review_status_email  # Import the email function

@receiver(pre_save, sender=User)
def handle_verification_status_change(sender, instance, **kwargs):
    if not instance.pk:
        # The instance is being created; no previous instance to compare
        return

    try:
        previous_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        # The instance is new; no previous data to compare
        return

    previous_status = previous_instance.verification_status
    current_status = instance.verification_status

    # Check if verification_status has changed to 'Refused' or 'Verified'
    if previous_status != current_status and current_status in ['Refused', 'Verified']:
        if current_status == 'Refused':
            # Remove sensitive information if the status is 'Refused'
            instance.phone_number = None
            if instance.government_id:
                instance.government_id.delete(save=False)  # Deletes the file
                instance.government_id = None
            instance.age = None
            instance.country_of_origin = None
            instance.university = None
            instance.course = None

        # Send email notification based on the verification status
        try:
            send_review_status_email(
                user_email=instance.email,
                user_name=f"{instance.first_name} {instance.last_name}",
                status=current_status.lower(),
            )
        except Exception as e:
            print("Exception while sending email:", e)
