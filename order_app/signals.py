from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from product_app.utils import send_sms
from django.conf import settings
from django.db.models import Sum
@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        owner_phone_number = settings.OWNER_PHONE_NUMBER
        message = f"New order submitted! Order ID: {instance.id}, Total Price: {instance.total_price}"
        send_sms(owner_phone_number, message)

@receiver(post_save, sender=Order)
def update_total_spent(sender, instance, created, **kwargs):
    user = instance.user
    total_spent = Order.objects.filter(user=user).aggregate(total=Sum('total_price'))['total'] or 0
    user.total_spent = total_spent
    user.save()