from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile whenever a new User is registered."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
