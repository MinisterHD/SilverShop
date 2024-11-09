from rest_framework import serializers
from .models import Order,CartItem,Cart,OrderItem,Wishlist, WishlistItem
from product_app.serializers import ProductSerializer
from product_app.models import Product
from django.db import transaction

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all()) 
    product_detail = ProductSerializer(read_only=True)
    is_preordered = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'product_detail', 'is_preordered']

    def create(self, validated_data):
        product = validated_data.pop('product')
        quantity = validated_data.pop('quantity')
        is_preordered = (product.stock < quantity) and product.pre_order_available
        
        order_item = OrderItem.objects.create(
            product=product,
            quantity=quantity,
            is_preordered=is_preordered,
            **validated_data
        )
        order_item.product_detail = ProductSerializer(product).data
        return order_item

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, required=False)
    total_price = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", 'user', 'user_first_name', 'user_last_name', 'user_phone_number',
            'shipped_at', 'delivery_address', 'delivery_status', 'total_price', 
            'order_date', 'order_items'
        ]
        read_only_fields = ['id', 'user', 'order_date', 'total_price']

    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            total_price = 0
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                is_preordered = (product.stock < quantity) and product.pre_order_available
                OrderItem.objects.create(order=order, product=product, quantity=quantity, is_preordered=is_preordered)
                price = product.pre_order_price if is_preordered else product.price_after_discount
                total_price += price * quantity

            order.total_price = total_price
            order.save()

        return order

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        preorder_items = []
        regular_items = []

        for item in instance.order_items.all():
            item_data = {
                'product': item.product.id,
                'quantity': item.quantity,
                'product_detail': ProductSerializer(item.product).data,
                'is_preordered': item.is_preordered
            }
            if item.is_preordered:
                preorder_items.append(item_data)
            else:
                regular_items.append(item_data)

        representation['preorder_items'] = preorder_items
        representation['regular_items'] = regular_items
        return representation


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        exclude = ['cart']

    def get_price(self, obj):
        return obj.product.pre_order_price if obj.is_preordered else obj.product.price_after_discount


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        total = 0
        for item in obj.cartitem_set.all():
            item_price = item.product.pre_order_price if item.is_preordered else item.product.price_after_discount
            total += item.quantity * item_price
        return total

    class Meta:
        model = Cart
        fields = ['total_price', 'id', 'user', 'created_at', 'items']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        preorder_items = []
        regular_items = []

        for item in instance.cartitem_set.all():
            item_data = {
                'product': item.product.id,
                'quantity': item.quantity,
                'product_detail': ProductSerializer(item.product).data,
                'is_preordered': item.is_preordered
            }
            if item.is_preordered:
                preorder_items.append(item_data)
            else:
                regular_items.append(item_data)

        representation['preorder_items'] = preorder_items
        representation['regular_items'] = regular_items

        representation.pop('items', None)
        
        return representation


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'items']


