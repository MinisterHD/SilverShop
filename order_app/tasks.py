from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order
from .utils import notify_user
from django.db import models
from order_app.models import PreOrderQueue
from .queue_management import reserve_for_first_in_queue
@shared_task
def update_delivery_status():
    seven_days_ago = timezone.now() - timedelta(days=7)
    orders = Order.objects.filter(delivery_status='shipped', shipped_at__lte=seven_days_ago)
    for order in orders:
        order.delivery_status = 'delivered'
        order.save()

# Updated check_reservation_expiry function
@shared_task
def check_reservation_expiry(queue_item_id):
    from order_app.models import PreOrderQueue

    try:
        queue_item = PreOrderQueue.objects.get(id=queue_item_id)
        if queue_item.reservation_status == 'reserved' and queue_item.reservation_expires_at < timezone.now():
            # Expired, move to the end of the queue
            product_queue = PreOrderQueue.objects.filter(product=queue_item.product)
            max_position = product_queue.aggregate(max_position=models.Max('position'))['max_position']
            queue_item.position = max_position + 1
            queue_item.reservation_status = 'expired'
            queue_item.save()

            # Notify the next user in line
            notify_user(queue_item.user, queue_item.product, queue_item.position)
            reserve_for_first_in_queue(queue_item.product.id)

    except PreOrderQueue.DoesNotExist:
        # Handle the case where the queue item does not exist anymore
        pass  # or log the error
