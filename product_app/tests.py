from django.test import TestCase
from unittest.mock import patch
from .models import Product, Category
from .utils import send_sms, notify_users
from order_app.models import WishlistItem, Wishlist
from user_app.models import User

class ProductStockUpdateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(phone_number='1234567890')
        self.category = Category.objects.create(name='Test Category', slugname='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            price=100,
            stock=0,
            category=self.category,
            slugname='test-product'
        )
        self.wishlist = Wishlist.objects.create(user=self.user)
        self.wishlist_item = WishlistItem.objects.create(wishlist=self.wishlist, product=self.product)

    @patch('product_app.utils.send_sms')
    def test_notify_users_on_stock_update(self, mock_send_sms):
        self.product.stock = 10
        self.product.save()
        mock_send_sms.assert_called_once_with(self.user.phone_number, f"Product {self.product.name} is now available!")

    @patch('product_app.utils.KavenegarAPI')
    def test_send_sms(self, MockKavenegarAPI):
        mock_api_instance = MockKavenegarAPI.return_value
        mock_api_instance.sms_send.return_value = {'status': 'sent'}

        response = send_sms('1234567890', 'Test message')
        mock_api_instance.sms_send.assert_called_once_with({
            'sender': '',
            'receptor': '1234567890',
            'message': 'Test message'
        })
        self.assertEqual(response, {'status': 'sent'})