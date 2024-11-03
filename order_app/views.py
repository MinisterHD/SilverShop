import logging
from rest_framework import status, filters,viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import JSONParser
from .models import *
from .serializers import OrderSerializer, CartSerializer,WishlistSerializer
from product_app.models import Product
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser
from .permissions import IsOwnerOrAdmin
from django.db import  transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.utils import timezone
logger = logging.getLogger(__name__)
from .utils import notify_user


#Order
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]
    ordering_fields = ['delivery_date', 'order_date']
    ordering = ['-order_date']
    
    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('order_items__product')
        params = self.request.query_params

        user_id = params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        delivery_status = params.get('delivery_status')
        if delivery_status:
            queryset = queryset.filter(delivery_status=delivery_status)

        order_date = params.get('order_date')
        if order_date:
            queryset = queryset.filter(order_date=order_date)

        ordering = params.get('ordering', '-order_date')
        queryset = queryset.order_by(ordering)

        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            user = self.request.user
            cart = Cart.objects.get(user=user)

            if not cart.cartitem_set.exists():
                raise ValidationError("Your cart is empty. Add items to your cart before placing an order.")

            # Prepare order_items data from the cart for the serializer
            order_items_data = [
                {'product': cart_item.product, 'quantity': cart_item.quantity}
                for cart_item in cart.cartitem_set.all()
            ]

            # Pass the order items to the serializer
            order = serializer.save(user=user, order_items=order_items_data)

            # Clear the cart after the order is saved
            cart.cartitem_set.all().delete()


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        previous_status = instance.delivery_status
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if previous_status == 'pending' and instance.delivery_status == 'shipped':
            instance.shipped_at = timezone.now()
            instance.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        try:
            order = self.get_object()
            if order.delivery_status != 'cancelled':
                order.cancel_order()
                return Response({"detail": "Order cancelled successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Order is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#Cart
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer(self, *args, **kwargs):
        serializer_class = CartSerializer
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=['post'], url_path='add', permission_classes=[IsAuthenticated])
    def add_to_cart(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                cart = self.get_cart(user)
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

                if product.stock >= quantity:
                    cart_item.is_preordered = False
                    cart_item.price = product.price_after_discount
                elif product.pre_order_available:
                    cart_item.is_preordered = True
                    cart_item.price = product.pre_order_price
                else:
                    raise ValidationError(f"Not enough stock for {product.name}, and pre-order is not available.")

                cart_item.quantity += quantity
                cart_item.save()

                cart_serializer = self.get_serializer(cart)
                return Response({
                    "detail": "Product added to cart." if product.stock >= quantity else "Product added as pre-order.",
                    "cart": cart_serializer.data
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='view-item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def retrieve_cart_item(self, request, product_id=None):
        user = request.user  
        try:
            cart_item = CartItem.objects.get(cart__user=user, product_id=product_id)
            cart_serializer = self.get_serializer(cart_item.cart)
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put', 'patch'], url_path='update-item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def update_cart_item(self, request, product_id=None):
        user = request.user  
        try:
            cart_item = CartItem.objects.get(cart__user=user, product_id=product_id)
            quantity = request.data.get('quantity')
            if quantity is None or quantity <= 0:
                return Response({"detail": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity
            cart_item.save()
            cart_serializer = self.get_serializer(cart_item.cart)
            return Response({
                "detail": "Cart item updated.",
                "cart": cart_serializer.data
            }, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='remove-item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def delete_cart_item(self, request, product_id=None):
        user = request.user  
        try:
            cart_item = CartItem.objects.get(cart__user=user, product_id=product_id)
            cart = cart_item.cart
            cart_item.delete()
            cart_serializer = self.get_serializer(cart)
            return Response({
                "detail": "Product removed from cart.",
                "cart": cart_serializer.data
            }, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='view-cart', permission_classes=[IsAuthenticated])
    def retrieve_cart(self, request):
        user = request.user  
        try:
            cart = Cart.objects.get(user=user)
            cart_serializer = self.get_serializer(cart)
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#WishList
class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_object(self):
        user = self.request.user
        try:
            wishlist, created = Wishlist.objects.get_or_create(user=user)
            return wishlist
        except Wishlist.DoesNotExist:
            raise NotFound(detail="Wishlist not found", code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving wishlist for user {user.id}: {str(e)}")
            raise

    @action(detail=False, methods=['post'], url_path='add', permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request):
        user = request.user  
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = get_object_or_404(Product, id=product_id)
            wishlist, created = Wishlist.objects.get_or_create(user=user)
            wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
            if created:
                return Response({"detail": "Product added to wishlist."}, status=status.HTTP_201_CREATED)
            else:
                return Response({"detail": "Product is already in the wishlist."}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except WishlistItem.MultipleObjectsReturned:
            return Response({"detail": "Product is already in the wishlist."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error adding product {product_id} to wishlist for user {user.id}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def remove_from_wishlist(self, request, product_id=None):
        user = request.user 
        try:
            wishlist = Wishlist.objects.get(user=user)
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product_id=product_id)
            wishlist_item.delete()
            return Response({"detail": "Product removed from wishlist."}, status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response({"detail": "Wishlist not found."}, status=status.HTTP_404_NOT_FOUND)
        except WishlistItem.DoesNotExist:
            return Response({"detail": "Product not found in wishlist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error removing product {product_id} from wishlist for user {user.id}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_all(self, request):
        try:
            queryset = self.get_queryset()

            user_id = request.query_params.get('id')
            if user_id:
                queryset = queryset.filter(user__id=user_id)

            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(user__id__icontains=search)

            ordering = request.query_params.get('ordering', 'id')
            queryset = queryset.order_by(ordering)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing wishlists: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs.get('pk')
        product_id = self.kwargs.get('product_id')

        try:
            wishlist = Wishlist.objects.get(user_id=user_id)
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, product_id=product_id)
            wishlist_item.delete()
            return Response({"detail": "Product removed from wishlist."}, status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response({"detail": "Wishlist not found."}, status=status.HTTP_404_NOT_FOUND)
        except WishlistItem.DoesNotExist:
            return Response({"detail": "Product not found in wishlist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error removing product {product_id} from wishlist for user {user_id}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


#PreOrder Payment
class PreOrderViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['post'], url_path='pay-remaining')
    def pay_remaining_amount(self, request, pre_order_id=None):
        user = request.user
        try:
            pre_order = PreOrderQueue.objects.get(id=pre_order_id, user=user)
        except PreOrderQueue.DoesNotExist:
            return Response({"detail": "Pre-order not found."}, status=status.HTTP_404_NOT_FOUND)

        remaining_amount = pre_order.total_amount_due - pre_order.paid_amount

        pre_order.paid_amount += remaining_amount
        pre_order.update_payment_status()

        return Response({"detail": "Remaining amount paid successfully."}, status=status.HTTP_200_OK)
    