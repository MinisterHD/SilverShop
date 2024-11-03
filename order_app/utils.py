from kavenegar import KavenegarAPI, APIException, HTTPException
from django.conf import settings
from .models import PreOrderQueue
from datetime import timedelta
from django.utils import timezone
def notify_user(phone_number, message):
    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'receptor': phone_number, 
            'message': message,
        }
        response = api.sms_send(params)
        print("SMS sent successfully:", response)
        
    except APIException as e:
        print("API Exception:", e)
    except HTTPException as e:
        print("HTTP Exception:", e)

def reserve_for_first_in_queue(product_id):
    # Get the first user in the queue for the specified product
    first_in_queue = PreOrderQueue.objects.filter(
        product_id=product_id, reservation_status='waiting'
    ).order_by('position').first()
    
    if first_in_queue:
        # Update the reservation status and set the expiration time
        first_in_queue.reservation_status = 'reserved'
        first_in_queue.reservation_expires_at = timezone.now() + timedelta(hours=4)  # Reservation expires in 4 hours
        first_in_queue.save()

        # Notify the user with payment link or instructions
        message = (
            f"Hello {first_in_queue.user.username}, your reserved product '{first_in_queue.product.name}' is now available. "
            "Please complete the remaining payment within 4 hours to secure your item."
        )
        notify_user(first_in_queue.user.phone_number, message)

        return first_in_queue.user  # Return the user for further processing if needed
    return None  # No user in the queue
