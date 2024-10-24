from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')  # Ensure this matches your URL name
        self.login_url = reverse('login')  # Ensure this matches your URL name

    def test_signup_sets_cookies(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'testuser@example.com'
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE'], response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies[settings.SIMPLE_JWT['AUTH_COOKIE']].get('httponly'))
        self.assertTrue(response.cookies['refresh_token'].get('httponly'))

    def test_login_sets_cookies(self):
        # First, create a user
        user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')

        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(settings.SIMPLE_JWT['AUTH_COOKIE'], response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies[settings.SIMPLE_JWT['AUTH_COOKIE']].get('httponly'))
        self.assertTrue(response.cookies['refresh_token'].get('httponly'))