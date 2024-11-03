from django.db import models
from user_app.models import User
from product_app.models import Product
from django.utils import timezone
from datetime import timedelta

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_address = models.TextField(blank=True, null=True)
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled')
        ],
        blank=False, null=False, default="pending"
    )
    total_price = models.PositiveIntegerField(default=0)
    order_date = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    products = models.ManyToManyField(Product, through='OrderItem')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.delivery_address and self.user.address:
            self.delivery_address = self.user.address
        super().save(*args, **kwargs)

    def cancel_order(self):
        for item in self.order_items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        self.delivery_status = 'cancelled'
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_preordered = models.BooleanField(default=False)
    total_amount = models.PositiveIntegerField(default=0)  
    paid_amount = models.PositiveIntegerField(default=0) 

    @property
    def remaining_balance(self):
        return self.total_amount - self.paid_amount  


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    is_preordered = models.BooleanField(default=False)
    price = models.PositiveIntegerField(default=0)


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s Wishlist"


class PreOrderQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE, related_name='preorder_queue')
    order_date = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField()
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    reservation_status = models.CharField(
        max_length=20,
        choices=[
            ('waiting', 'Waiting'),
            ('reserved', 'Reserved'),
            ('expired', 'Expired'),
            ('fully_paid', 'Fully Paid')
        ],
        default="waiting"
    )
    paid_amount = models.PositiveIntegerField(default=0) 
    total_amount_due = models.PositiveIntegerField(default=0) 

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['position']

    def __str__(self):
        return f"User {self.user.id} in queue for Product {self.product.id} at position {self.position}"
    
    def save(self, *args, **kwargs):
        if not self.paid_amount:
            self.paid_amount = self.product.pre_order_price
        if not self.total_amount_due:
            self.total_amount_due = self.product.price_after_discount - self.product.pre_order_price
        super().save(*args, **kwargs)

    def update_payment_status(self):
        if self.paid_amount >= self.total_amount_due:
            self.reservation_status = 'fully_paid'
        else:
            self.reservation_status = 'waiting'
        self.save()