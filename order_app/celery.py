from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SilverShop.settings')

app = Celery('SilverShop')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.worker_pool = 'gevent'


app.conf.beat_schedule = {
    'check-reservation-every-minute': {
        'task': 'order_app.queue_management.check_reservations',  
        'schedule': 60.0,  
    },
}

app.conf.timezone = 'Asia/Tehran'  
