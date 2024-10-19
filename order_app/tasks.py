from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order

@shared_task
def update_delivery_status():
    seven_days_ago = timezone.now() - timedelta(days=7)
    orders = Order.objects.filter(delivery_status='shipped', shipped_at__lte=seven_days_ago)
    for order in orders:
        order.delivery_status = 'delivered'
        order.save()