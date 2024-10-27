import logging
from kavenegar import *
from django.conf import settings
from order_app.models import WishlistItem

logger = logging.getLogger(__name__)

def send_sms(phone_number, message):
    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'sender': '',  
            'receptor': phone_number,
            'message': message
        }
        response = api.sms_send(params)
        return response
    except APIException as e:
        logger.error(f"Kavenegar APIException: {e}")
    except HTTPException as e:
        logger.error(f"Kavenegar HTTPException: {e}")

def notify_users(product):
    logger.info(f"Notifying users about product availability: {product.name}")
    wishlist_items = WishlistItem.objects.filter(product=product)
    notified_users = set()  

    for item in wishlist_items:
        user = item.wishlist.user
        if user.id not in notified_users:
            logger.info(f"Sending SMS to user {user.id}")

            message = f"Product {product.name} is now available!"
            phone_number = user.phone_number

            logger.info("Calling send_sms function")
            send_sms(phone_number, message)
            logger.info("send_sms function called successfully")

            notified_users.add(user.id)