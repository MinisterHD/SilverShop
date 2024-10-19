from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Category, Subcategory, Product, Comment, Rating
from user_app.models import User

class CategoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.category_data = {
            'translations': {
                'en': {'name': 'Electronics'},
                'fa': {'name': 'الکترونیک'}
            },
            'slugname': 'electronics'
        }

    def test_create_category(self):
        url = reverse('create-category')
        response = self.client.post(url, self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().slugname, 'electronics')

    def test_list_categories(self):
        Category.objects.create(slugname='electronics')
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_category(self):
        category = Category.objects.create(slugname='electronics')
        url = reverse('category-detail', args=[category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slugname'], 'electronics')

class SubcategoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.category = Category.objects.create(slugname='electronics')
        self.subcategory_data = {
            'translations': {
                'en': {'name': 'Mobile Phones'},
                'fa': {'name': 'تلفن همراه'}
            },
            'slugname': 'mobile-phones',
            'category': self.category.id
        }

    def test_create_subcategory(self):
        url = reverse('create-subcategory')
        response = self.client.post(url, self.subcategory_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subcategory.objects.count(), 1)
        self.assertEqual(Subcategory.objects.get().slugname, 'mobile-phones')

    def test_list_subcategories(self):
        Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        url = reverse('subcategory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_subcategory(self):
        subcategory = Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        url = reverse('subcategory-detail', args=[subcategory.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slugname'], 'mobile-phones')

class ProductTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.category = Category.objects.create(slugname='electronics')
        self.subcategory = Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        self.product_data = {
            'translations_en_name': 'iPhone',
            'translations_en_description': 'Apple iPhone',
            'translations_fa_name': 'آیفون',
            'translations_fa_description': 'آیفون اپل',
            'slugname': 'iphone',
            'price': 100000,  # Price in cents
            'stock': 10,
            'category': self.category.id,
            'subcategory': self.subcategory.id
        }

    def test_create_product(self):
        url = reverse('create-product')
        response = self.client.post(url, self.product_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.get().slugname, 'iphone')

    def test_list_products(self):
        Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_product(self):
        product = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        url = reverse('product-detail', args=[product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slugname'], 'iphone')

    def test_update_product(self):
        product = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        url = reverse('product-detail', args=[product.id])
        data = {'slugname': 'updated-iphone'}
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.slugname, 'updated-iphone')

    def test_delete_product(self):
        product = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        url = reverse('product-detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)

class CommentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.category = Category.objects.create(slugname='electronics')
        self.subcategory = Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        self.product = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        self.comment_data = {
            'text': 'Great product!',
            'product': self.product.id,
            'owner': self.user.id
        }

    def test_create_comment(self):
        url = reverse('create-comment')
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get().text, 'Great product!')

    def test_list_comments(self):
        Comment.objects.create(text='Great product!', product=self.product, owner=self.user)
        url = reverse('comment-list', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_comment(self):
        comment = Comment.objects.create(text='Great product!', product=self.product, owner=self.user)
        url = reverse('comment-detail', args=[comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Great product!')

    def test_update_comment(self):
        comment = Comment.objects.create(text='Great product!', product=self.product, owner=self.user)
        url = reverse('comment-detail', args=[comment.id])
        data = {'text': 'Updated comment'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'Updated comment')

    def test_delete_comment(self):
        comment = Comment.objects.create(text='Great product!', product=self.product, owner=self.user)
        url = reverse('comment-detail', args=[comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

class RatingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.category = Category.objects.create(slugname='electronics')
        self.subcategory = Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        self.product = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory)
        self.rating_data = {
            'rating': 5,
            'product': self.product.id,
            'user': self.user.id
        }

    def test_create_rating(self):
        url = reverse('create-rating')
        response = self.client.post(url, self.rating_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.get().rating, 5)

    def test_list_ratings(self):
        Rating.objects.create(rating=5, product=self.product, user=self.user)
        url = reverse('rating-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_rating(self):
        rating = Rating.objects.create(rating=5, product=self.product, user=self.user)
        url = reverse('rating-detail', args=[rating.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)

    def test_update_rating(self):
        rating = Rating.objects.create(rating=5, product=self.product, user=self.user)
        url = reverse('rating-detail', args=[rating.id])
        data = {'rating': 4}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rating.refresh_from_db()
        self.assertEqual(rating.rating, 4)

    def test_delete_rating(self):
        rating = Rating.objects.create(rating=5, product=self.product, user=self.user)
        url = reverse('rating-detail', args=[rating.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Rating.objects.count(), 0)


class TopSellerTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(slugname='electronics')
        self.subcategory = Subcategory.objects.create(slugname='mobile-phones', category=self.category)
        self.product1 = Product.objects.create(slugname='iphone', price=100000, stock=10, category=self.category, subcategory=self.subcategory, sales_count=50)
        self.product2 = Product.objects.create(slugname='samsung', price=80000, stock=15, category=self.category, subcategory=self.subcategory, sales_count=30)

    def test_top_seller_products(self):
        url = reverse('top-seller')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['slugname'], 'iphone')
        self.assertEqual(response.data['results'][1]['slugname'], 'samsung')