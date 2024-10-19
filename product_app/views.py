from rest_framework import viewsets
from django.db.models import Q
from .models import *
from .serializers import *
from .permissions import *
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,IsAdminUser
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError, NotFound
from parler.utils.context import activate, switch_language
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
# Category
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def create(self, request, *args, **kwargs):
        language = request.data.get('language', 'en')
        activate(language)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        if 'slugname' in params:
            queryset = queryset.filter(slugname=params['slugname'])

        language = params.get('language', 'en')
        queryset = queryset.active_translations(language_code=language)
        
        return queryset

    def get_object(self):
        language = self.request.query_params.get('language', 'en')
        obj = super().get_object()

        with switch_language(obj, language):
            return obj

    def retrieve(self, request, *args, **kwargs):
        language = request.query_params.get('language', 'en')
        try:
            obj = self.get_object()
            with switch_language(obj, language):
                serializer = self.get_serializer(obj)
                return Response(serializer.data)
        except Http404:
            raise NotFound('Category not found.')
        except Exception as e:
            return Response({'error': f'An error occurred while retrieving the category: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        language = request.data.get('language', 'en')
        obj = self.get_object()
        with switch_language(obj, language):
            return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': f'An error occurred while deleting the category: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# SubCategory
class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]
    lookup_url_kwarg = 'subcategory_id'

    def create(self, request, *args, **kwargs):
        language = request.data.get('language', 'en')
        activate(language)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if 'category' in params:
            category_id = params['category']
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound('SubCategory not found.')

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': f'An error occurred while retrieving the SubCategory: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An error occurred while updating the SubCategory: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': f'An error occurred while deleting the Subcategory: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Products
class ProductPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, JSONParser]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    lookup_url_kwarg = 'product_id'

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        language = request.data.get('language', 'en')
        activate(language)
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            transaction.set_rollback(True)
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            transaction.set_rollback(True)
            return Response({'error': f'An error occurred while creating the product: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        category_id = params.get('category')
        subcategory_id = params.get('subcategory')
        if category_id or subcategory_id:
            try:
                if category_id:
                    Category.objects.get(id=category_id)
                if subcategory_id:
                    Subcategory.objects.get(id=subcategory_id)
            except (Category.DoesNotExist, Subcategory.DoesNotExist):
                raise ValidationError("Invalid category or subcategory ID(s) provided.")

        if category_id or subcategory_id:
            queryset = queryset.filter(Q(category_id=category_id) | Q(subcategory_id=subcategory_id))

        min_price = params.get('minPrice')
        max_price = params.get('maxPrice')
        if min_price and max_price:
            queryset = queryset.filter(price_after_discount__gte=float(min_price), price_after_discount__lte=float(max_price))
        elif min_price:
            queryset = queryset.filter(price_after_discount__gte=float(min_price))
        elif max_price:
            queryset = queryset.filter(price_after_discount__lte=float(max_price))

        sort_field = params.get('sort', 'category')
        if sort_field:
            queryset = queryset.order_by(sort_field)

        sort_order = params.get('sort_order', 'asc')
        if sort_order == 'desc':
            queryset = queryset.order_by('-price_after_discount')
        else:
            queryset = queryset.order_by('price_after_discount')

        return queryset

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound('Product not found.')

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': f'An error occurred while retrieving the Product: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'validation_errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An error occurred while updating the Product: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': f'An error occurred while deleting the Product: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Comments
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]
    lookup_url_kwarg = 'comment_id'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f'An error occurred while creating the comment: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return self.queryset.filter(product_id=product_id)
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'An error occurred while retrieving the comment: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An error occurred while updating the comment: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Http404:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'An error occurred while deleting the comment: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Rating
class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'user']
    lookup_url_kwarg = 'rating_id'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RatingCreateSerializer if self.action == 'create' else RatingUpdateSerializer
        return RatingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            product_id = serializer.validated_data['product'].id
            if Rating.objects.filter(user=request.user, product_id=product_id).exists():
                return Response({"error": "You have already rated this product."}, status=status.HTTP_400_BAD_REQUEST)

            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f'An error occurred while creating the rating: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        product_id = params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        user_id = params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            return Response({'error': 'Rating not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'An error occurred while retrieving the rating: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': 'You do not have permission to update this rating.'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': f'An error occurred while updating the rating: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Http404:
            return Response({'error': 'Rating not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'An error occurred while deleting the rating: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)       

#TopSellerProducts
class TopSellerAPIView(ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.order_by('-sales_count')[:10]


