from rest_framework import serializers
from .models import Order,CartItem,Cart,OrderItem,Wishlist, WishlistItem
from product_app.serializers import ProductSerializer,ProductDetailSerializer
from product_app.models import Product
from django.db import transaction

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all()) 
    product_detail=ProductDetailSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity','product_detail']
    def create(self, validated_data):
        product = validated_data.pop('product')
        quantity = validated_data.pop('quantity')

        order_item = OrderItem.objects.create(product=product, quantity=quantity, **validated_data)
        order_item.product_detail = ProductDetailSerializer(product).data
        return order_item

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    total_price = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True) 
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    class Meta:
        model = Order
        fields = ["id",'user', 'user_first_name', 'user_last_name', 'user_phone_number','shipped_at', 'delivery_address', 'delivery_status', 'total_price', 'order_date', 'delivery_date', 'order_items']
        read_only_fields = ['id', 'user', 'order_date', 'total_price']  
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            total_price = 0
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                OrderItem.objects.create(order=order, product=product, quantity=quantity)
                total_price += product.price * quantity

            order.total_price = total_price
            order.save()

        return order

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['order_items'] = [
            {
                'product': item.product.id,
                'quantity': item.quantity,
                'product_detail': ProductDetailSerializer(item.product).data
            }
            for item in instance.order_items.all()
        ]
        return representation

    def update(self, instance, validated_data):
        order_items_data = validated_data.pop('order_items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if order_items_data is not None:
            instance.order_items.all().delete()
            total_price = 0
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                OrderItem.objects.create(order=instance, product=product, quantity=quantity)
                total_price += product.price * quantity

            instance.total_price = total_price

        instance.save()
        return instance

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) 

    class Meta:
        model = CartItem
        exclude = ['cart'] 

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True)  

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items'] 

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