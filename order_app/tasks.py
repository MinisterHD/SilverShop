from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import models, transaction
import logging
from .models import Order
from .utils import notify_user,reserve_for_first_in_queue
from order_app.models import PreOrderQueue

logger = logging.getLogger(__name__)

@shared_task
def update_delivery_status():
    seven_days_ago = timezone.now() - timedelta(days=7)
    orders = Order.objects.filter(delivery_status='shipped', shipped_at__lte=seven_days_ago)
    for order in orders:
        order.delivery_status = 'delivered'
        order.save()

@shared_task
def check_reservation_expiry(queue_item_id):
    from order_app.models import PreOrderQueue

    try:
        queue_item = PreOrderQueue.objects.get(id=queue_item_id)
        if queue_item.reservation_status == 'reserved' and queue_item.reservation_expires_at < timezone.now():
            # Expired - move to the end of the queue
            with transaction.atomic():
                product_queue = PreOrderQueue.objects.filter(product=queue_item.product)
                max_position = product_queue.aggregate(max_position=models.Max('position'))['max_position']
                
                # Update reservation status and position
                queue_item.position = max_position + 1
                queue_item.reservation_status = 'expired'
                queue_item.save()

            # Notify the next user in line and reserve for them
            next_user = reserve_for_first_in_queue(queue_item.product.id)
            if next_user:
                notify_user(next_user, queue_item.product, next_user.position)

    except PreOrderQueue.DoesNotExist:
        logger.warning(f"Queue item with ID {queue_item_id} does not exist.")
    except Exception as e:
        logger.error(f"Error in check_reservation_expiry for queue item {queue_item_id}: {str(e)}")