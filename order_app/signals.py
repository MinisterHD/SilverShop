from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from product_app.utils import send_sms
from django.conf import settings

@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        owner_phone_number = settings.OWNER_PHONE_NUMBER
        message = f"New order submitted! Order ID: {instance.id}, Total Price: {instance.total_price}"
        send_sms(owner_phone_number, message)