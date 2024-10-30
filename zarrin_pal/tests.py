from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from order_app.models import Cart, CartItem
from product_app.models import Product, Category
from user_app.models import User
from django.utils import timezone
import json


class PaymentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(phone_number='09011111111', otp='123456', otp_expiration=timezone.now() + timezone.timedelta(minutes=5))
        
        self.category = Category.objects.create(name='Test Category', slugname='test-category')
        self.product = Product.objects.create(name='Test Product', slugname='test-product', price=1000, stock=10, category=self.category)
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def authenticate_user(self):
        # Simulate sending OTP
        response = self.client.post(reverse('send-otp'), json.dumps({'phone_number': self.user.phone_number}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Simulate verifying OTP
        response = self.client.post(reverse('check-otp'), json.dumps({'phone_number': self.user.phone_number, 'otp': self.user.otp}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['tokens']['access'])

    @patch('zarrin_pal.views.requests.post')
    def test_initiate_payment(self, mock_post):
        self.authenticate_user()

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'Status': 100, 'Authority': 'test_authority'}

        response = self.client.post(reverse('request'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('url', response.data)
        self.assertIn('authority', response.data)
        self.assertEqual(response.data['authority'], 'test_authority')

        # Verify that the correct amount was sent in the request
        expected_amount = self.cart_item.quantity * self.product.price
        request_data = json.loads(mock_post.call_args[1]['data'])
        self.assertEqual(request_data['Amount'], expected_amount)