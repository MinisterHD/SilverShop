from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Order, OrderItem, Cart, CartItem
from product_app.models import Product, Category
from user_app.models import User

class OrderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        

        self.category = Category.objects.create(name='Test Category',slugname="yaser")

        self.product1 = Product.objects.create(name='Product 1', price=100, stock=10, category=self.category)
        self.product2 = Product.objects.create(name='Product 2', price=200, stock=5, category=self.category)
        
        self.order_data = {
            'delivery_address': '123 Test St',
            'order_items': [
                {'product': self.product1.id, 'quantity': 2},
                {'product': self.product2.id, 'quantity': 1}
            ]
        }

    def test_create_order(self):
        url = reverse('order-create')
        response = self.client.post(url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)

    def test_list_orders(self):
        Order.objects.create(user=self.user, delivery_address='123 Test St', delivery_status='pending', total_price=300)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_order(self):
        order = Order.objects.create(user=self.user, delivery_address='123 Test St', delivery_status='pending', total_price=300)
        url = reverse('order-detail', args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['delivery_address'], '123 Test St')

    def test_update_order(self):
        order = Order.objects.create(user=self.user, delivery_address='123 Test St', delivery_status='pending', total_price=300)
        url = reverse('order-detail', args=[order.id])
        data = {'delivery_address': '456 New St'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.delivery_address, '456 New St')

    def test_delete_order(self):
        order = Order.objects.create(user=self.user, delivery_address='123 Test St', delivery_status='pending', total_price=300)
        url = reverse('order-detail', args=[order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    def test_cancel_order(self):
        order = Order.objects.create(user=self.user, delivery_address='123 Test St', delivery_status='pending', total_price=300)
        url = reverse('cancel-order', args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.delivery_status, 'cancelled')

class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        
        # Create a category
        self.category = Category.objects.create(name='Test Category')
        
        # Create products with the category
        self.product1 = Product.objects.create(name='Product 1', price=100, stock=10, category=self.category)
        self.product2 = Product.objects.create(name='Product 2', price=200, stock=5, category=self.category)

    def test_add_to_cart(self):
        url = reverse('add-to-cart')
        data = {'product_id': self.product1.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_retrieve_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        url = reverse('cart-item-detail', args=[self.user.id, self.product1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['product']['id'], self.product1.id)

    def test_update_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        url = reverse('cart-item-detail', args=[self.user.id, self.product1.id])
        data = {'quantity': 5}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

    def test_delete_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        url = reverse('cart-item-detail', args=[self.user.id, self.product1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_retrieve_user_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        url = reverse('user-cart', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['product']['id'], self.product1.id)