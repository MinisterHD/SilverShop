import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Product
from .utils import notify_users

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Product)
def calculate_price_after_discount(sender, instance, **kwargs):
    if instance.price and instance.discount_percentage:
        discount = instance.discount_percentage / 100
        instance.price_after_discount = instance.price * (1 - discount)
        logger.info(f"Calculated price after discount for product {instance.id}: {instance.price_after_discount}")

@receiver(pre_save, sender=Product)
def product_stock_update(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            instance._old_stock = old_product.stock  
        except Product.DoesNotExist:
            instance._old_stock = None
    else:
        instance._old_stock = None

@receiver(post_save, sender=Product)
def notify_stock_update(sender, instance, **kwargs):
    logger.info(f"Product {instance.id} saved with stock {instance.stock}")
    if instance._old_stock is not None:
        logger.info(f"Old stock for product {instance.id}: {instance._old_stock}")
        logger.info(f"New stock for product {instance.id}: {instance.stock}")
        if instance._old_stock == 0 and instance.stock > 0:
            logger.info(f"Stock updated from 0 to {instance.stock} for product {instance.id}, notifying users")
            notify_users(instance)
        else:
            logger.info(f"No stock change from 0 to positive for product {instance.id}")
    else:
        logger.info(f"New product {instance.id} created with stock {instance.stock}")