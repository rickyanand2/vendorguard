# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Organization, Membership

User = get_user_model()


@receiver(post_save, sender=User)
def assign_default_org_to_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        # Check if membership already exists using try-except
        try:
            instance.membership
            return  # already has membership, exit early
        except Membership.DoesNotExist:
            pass

        # Create or get a default org
        org_name = f"{instance.email.split('@')[0].capitalize()} Admin Org"
        organization, _ = Organization.objects.get_or_create(name=org_name)
        Membership.objects.create(
            user=instance, organization=organization, role="owner"
        )
