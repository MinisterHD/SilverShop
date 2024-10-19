from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    CartViewSet,
    WishlistViewSet,
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
urlpatterns = [
    path('', include(router.urls)),
    #path('orders/', OrderListAPIView.as_view(), name='order-list'),
    #path('orders/create/', CreateOrderAPIView.as_view(), name='order-create'),
    #path('orders/<int:pk>/', OrderAPIView.as_view(), name='order-detail'),
    #path('orders/cancel/<int:order_id>/', CancelOrderAPIView.as_view(), name='cancel-order'),
    #path('orders/user/<int:user_id>/', UserOrdersAPIView.as_view(), name='user-orders'),

    
    
    #path('cart/add/', AddToCartAPIView.as_view(), name='add-to-cart'),
    #path('cart/<int:user_id>/item/<int:product_id>/', CartItemAPIView.as_view(), name='cart-item-detail'),
    #path('cart/<int:user_id>/', UserCartAPIView.as_view(), name='user-cart'),


    #path('wishlist/<int:user_id>/', WishlistAPIView.as_view(), name='wishlist'),
    #path('wishlist/<int:user_id>/add/', AddToWishlistAPIView.as_view(), name='add-to-wishlist'),
    #path('wishlists/', AdminWishlistListAPIView.as_view(), name='admin-wishlist-list'),
    #path('wishlist/<int:user_id>/remove/<int:product_id>/', RemoveFromWishlistAPIView.as_view(), name='remove-from-wishlist'),
  ]
