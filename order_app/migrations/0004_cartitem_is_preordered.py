# Generated by Django 5.1.2 on 2024-10-29 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_app', '0003_remove_order_delivery_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='is_preordered',
            field=models.BooleanField(default=False),
        ),
    ]
