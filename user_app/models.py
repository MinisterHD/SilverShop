from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = None 
    password=None
    phone_number = models.CharField(max_length=11, unique=True, null=False, blank=False,default='00000000000')
    address = models.TextField(null=True, blank=True)
    groups = models.ManyToManyField('auth.Group', related_name='my_user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='my_user_permissions', blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiration = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    total_spent = models.PositiveIntegerField( default=0) 
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number