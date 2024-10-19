from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    phone_number = models.CharField(max_length=11, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    groups = models.ManyToManyField('auth.Group', related_name='my_user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='my_user_permissions', blank=True)
