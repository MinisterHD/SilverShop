
from .models import PreOrderQueue
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from .utils import notify_user 
from django.db import models


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
    
    # Notify the user that they have entered the queue
    message = f"You are position {position} in the queue for {product.name}. We will notify you when your item is ready for purchase."
    notify_user(user.phone_number, message)


@shared_task
def check_reservations():
    now = timezone.now()
    expired_reservations = PreOrderQueue.objects.filter(
        reservation_expires_at__lt=now, reservation_status="waiting"
    )
    
    for reservation in expired_reservations:
        # Move the user to the end of the queue
        reservation.position = PreOrderQueue.objects.filter(product=reservation.product).count() + 1
        reservation.save()


