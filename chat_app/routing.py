from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<int:other_user_id>/', ChatConsumer.as_asgi()),
]