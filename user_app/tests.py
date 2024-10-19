from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User

class AuthTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.user_list_url = reverse('user-list')
        self.user_detail_url = lambda pk: reverse('user-detail', args=[pk])
        self.token_refresh_url = reverse('token-refresh')

        self.user_data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',
            'address': '123 Test St'
        }

        self.user = User.objects.create_user(
            username='existinguser',
            password='existingpassword',
            email='existinguser@example.com'
        )

    def test_signup(self):
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(username='testuser').email, 'testuser@example.com')

    def test_signup_existing_username(self):
        self.user_data['username'] = 'existinguser'
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['errors'])

    def test_login(self):
        response = self.client.post(self.login_url, {'username': 'existinguser', 'password': 'existingpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {'username': 'existinguser', 'password': 'wrongpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_logout(self):
        self.client.login(username='existinguser', password='existingpassword')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_token_refresh(self):
        response = self.client.post(self.login_url, {'username': 'existinguser', 'password': 'existingpassword'}, format='json')
        refresh_token = response.data['token']['refresh']
        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

class UserManagementTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='adminuser',
            password='adminpassword',
            email='adminuser@example.com',
            is_staff=True
        )
        self.client.login(username='adminuser', password='adminpassword')
        self.user_list_url = reverse('user-list')
        self.user_detail_url = lambda pk: reverse('user-detail', args=[pk])

    def test_list_users(self):
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_user(self):
        response = self.client.get(self.user_detail_url(self.user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'adminuser')

    def test_update_user(self):
        data = {'first_name': 'Updated'}
        response = self.client.patch(self.user_detail_url(self.user.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_delete_user(self):
        response = self.client.delete(self.user_detail_url(self.user.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)