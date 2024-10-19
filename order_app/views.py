import logging
from rest_framework import status, filters,viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import OrderSerializer, CartSerializer,WishlistSerializer
from product_app.models import Product
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser
from .permissions import IsOwnerOrAdmin
from django.db import  transaction
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.utils import timezone
logger = logging.getLogger(__name__)


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

#Order
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['delivery_status', 'order_date', 'user']
    ordering_fields = ['delivery_date', 'order_date']
    ordering = ['-order_date']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('order_items__product')
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(user=self.request.user)
            total_price = 0
            for item_data in self.request.data.get('order_items', []):
                product = Product.objects.get(id=item_data['product'])
                quantity = item_data['quantity']
                if product.stock < quantity:
                    raise ValidationError(f"Not enough stock for {product.name}.")
                OrderItem.objects.create(order=order, product=product, quantity=quantity)
                product.stock -= quantity
                product.sales_count += quantity
                product.save()
                total_price += product.price * quantity
            order.total_price = total_price
            order.save()

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

    @action(detail=False, methods=['post'], url_path='add', permission_classes=[IsAuthenticated])
    def add_to_cart(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if quantity <= 0:
            return Response({"detail": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                cart = self.get_cart(user)
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                cart_item.quantity += quantity
                cart_item.save()
                cart_serializer = CartSerializer(cart)
                return Response({
                    "detail": "Product added to cart.",
                    "cart": cart_serializer.data
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def retrieve_cart_item(self, request, pk=None, product_id=None):
        try:
            cart_item = CartItem.objects.get(cart__user_id=pk, product_id=product_id)
            cart_serializer = CartSerializer(cart_item.cart)
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['put', 'patch'], url_path='item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def update_cart_item(self, request, pk=None, product_id=None):
        try:
            cart_item = CartItem.objects.get(cart__user_id=pk, product_id=product_id)
            quantity = request.data.get('quantity')
            if quantity is None or quantity <= 0:
                return Response({"detail": "Invalid quantity."}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity
            cart_item.save()
            cart_serializer = CartSerializer(cart_item.cart)
            return Response({
                "detail": "Cart item updated.",
                "cart": cart_serializer.data
            }, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='item/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def delete_cart_item(self, request, pk=None, product_id=None):
        try:
            cart_item = CartItem.objects.get(cart__user_id=pk, product_id=product_id)
            cart = cart_item.cart
            cart_item.delete()
            cart_serializer = CartSerializer(cart)
            return Response({
                "detail": "Product removed from cart.",
                "cart": cart_serializer.data
            }, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='', permission_classes=[IsAuthenticated])
    def retrieve_cart(self, request, pk=None):
        try:
            cart = Cart.objects.get(user_id=pk)
            cart_serializer = CartSerializer(cart)
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user__username']
    search_fields = ['user__username']
    ordering_fields = ['user__username']
    ordering = ['user__username']

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            wishlist, created = Wishlist.objects.get_or_create(user_id=user_id)
            return wishlist
        except Wishlist.DoesNotExist:
            raise NotFound(detail="Wishlist not found", code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving wishlist for user {user_id}: {str(e)}")
            raise

    @action(detail=True, methods=['post'], url_path='add', permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request, pk=None):
        user_id = pk
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = get_object_or_404(Product, id=product_id)
            wishlist, created = Wishlist.objects.get_or_create(user_id=user_id)
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
            logger.error(f"Error adding product {product_id} to wishlist for user {user_id}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='remove/(?P<product_id>[^/.]+)', permission_classes=[IsAuthenticated])
    def remove_from_wishlist(self, request, pk=None, product_id=None):
        user_id = pk
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

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_all(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing wishlists: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    permission_classes = [IsOwnerOrAdmin]

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
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