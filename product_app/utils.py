from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from order_app.models import WishlistItem
import logging

logger = logging.getLogger(__name__)

def notify_users(product):
    logger.info(f"Notifying users about product availability: {product.name}")
    wishlist_items = WishlistItem.objects.filter(product=product)
    notified_users = set()  

    for item in wishlist_items:
        user = item.wishlist.user
        if user.id not in notified_users:
            logger.info(f"Sending email to user {user.id}")
 
            subject = f"Product {product.name} is now available!"
            html_message = render_to_string('email/product_available.html', {'product': product, 'user': user})
            plain_message = strip_tags(html_message)
            from_email = 'webmaster@example.com'  
            to = user.email

            logger.info("Calling send_mail function")
            send_mail(subject, plain_message, from_email, [to], html_message=html_message)
            logger.info("send_mail function called successfully")

            notified_users.add(user.id)  