from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.models import User
from apps.restaurant.models import Customer, Restaurant


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.role == User.ROLE.CUSTOMER:
#             Customer.objects.create(user=instance)
#         elif instance.role == User.ROLE.RESTAURANT:
#             Restaurant.objects.create(user=instance)