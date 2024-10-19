from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet
from .routing import websocket_urlpatterns  

router = DefaultRouter()
router.register(r'chatmessages', ChatMessageViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]


urlpatterns += websocket_urlpatterns