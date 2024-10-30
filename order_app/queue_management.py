# order_app/queue_management.py
from .models import PreOrderQueue
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from .utils import notify_user
@shared_task
def create_queue(user, product):
    # Get the current position in the queue
    position = PreOrderQueue.objects.filter(product=product).count() + 1

    # Calculate reservation expiration time
    reservation_expires_at = timezone.now() + timedelta(hours=4)

    # Create a new queue entry
    PreOrderQueue.objects.create(
        user=user,
        product=product,
        position=position,
        reservation_expires_at=reservation_expires_at
    )
    
    # Here, you can add code to send SMS notification to the user
    notify_user(user, product, position)

def check_reservations():
    now = timezone.now()
    expired_reservations = PreOrderQueue.objects.filter(reservation_expires_at__lt=now, reservation_status="waiting")
    
    for reservation in expired_reservations:
        # Move the user to the end of the queue or handle as needed
        reservation.position = PreOrderQueue.objects.filter(product=reservation.product).count() + 1
        reservation.save()



def reserve_for_first_in_queue(product_id):
    # Get the first user in the queue for the specified product
    first_in_queue = PreOrderQueue.objects.filter(product_id=product_id, reservation_status='waiting').order_by('position').first()
    
    if first_in_queue:
        # Update the reservation status and set the expiration time
        first_in_queue.reservation_status = 'reserved'
        first_in_queue.reservation_expires_at = timezone.now() + timedelta(hours=4) 
        first_in_queue.save()

        # Notify the user
        notify_user(first_in_queue.user, first_in_queue.product, first_in_queue.position)

        return first_in_queue.user  # Return the user for further processing if needed
    return None  # No user in the queue
