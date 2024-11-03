from django.db import models
from user_app.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    slugname = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    slugname = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return self.name

class Rating(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'),
                                          (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.rating} by {self.user}'

class Product(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField(max_length=2000, null=True, blank=True)
    brand = models.CharField(max_length=50, default='No Brand', null=True, blank=True)
    slugname = models.SlugField(max_length=255, unique=True, default='default-slug')
    price = models.PositiveIntegerField(null=False, blank=False)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], 
        default=0
    )
    price_after_discount = models.PositiveIntegerField(null=True, blank=True)
    stock = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, blank=True, null=True)

    pre_order_price=models.PositiveIntegerField(null=True, blank=True)
    pre_order_available = models.BooleanField(default=True)

    image1 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products/images/', blank=True, null=True)

    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sales_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    
    def get_image_urls(self, request):
        urls = []
        if self.image1:
            urls.append(request.build_absolute_uri(self.image1.url))
        if self.image2:
            urls.append(request.build_absolute_uri(self.image2.url))
        if self.image3:
            urls.append(request.build_absolute_uri(self.image3.url))
        if self.image4:
            urls.append(request.build_absolute_uri(self.image4.url))
        return urls

class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments', null=False, blank=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=200, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.owner} on {self.product}'