from .models import *
from .serializers import *
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import JSONParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.translation import gettext_lazy as _
import logging
from .permissions import IsOwnerOrAdmin
from rest_framework.generics import CreateAPIView
from django.conf import settings
from datetime import datetime, timedelta,timezone

logger = logging.getLogger(__name__)

class SignUpView(CreateAPIView):
    serializer_class = UserSignUpSerializer
    parser_classes = [JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            username = serializer.validated_data['username']

            if User.objects.filter(username=username).exists():
                raise ValidationError({'username': _('Username already exists.')})

            serializer.validated_data['password'] = make_password(serializer.validated_data['password'])
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Create response data
            response_data = {
                'user': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': access_token,
                }
            }

            # Set expiration times for access and refresh tokens
            access_token_expiration = datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            refresh_token_expiration = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

            # Create response and set cookies for tokens
            response = Response(data=response_data, status=status.HTTP_201_CREATED)
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                expires=access_token_expiration  
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                expires=refresh_token_expiration  
            )
            return response

        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error during sign up: {str(e)}")
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# User Login View
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            # Validate the serializer data
            serializer.is_valid(raise_exception=True)

            # Create the response with validated data
            response = Response(serializer.validated_data, status=status.HTTP_200_OK)

            # Get current time in UTC with time zone awareness
            current_time = datetime.now(timezone.utc)

            # Set cookies for access and refresh tokens with proper expiration
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=serializer.validated_data['token']['access'],
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                expires=current_time + timedelta(days=7)  # Set the expiration for 7 days
            )
            response.set_cookie(
                key='refresh_token',
                value=serializer.validated_data['token']['refresh'],
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                expires=current_time + timedelta(days=7)  # Set the expiration for 7 days
            )

            return response

        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error during login: {str(e)}')
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        try:
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            response = Response(data={'message': f'Bye {request.user.username}!'}, status=status.HTTP_204_NO_CONTENT)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.delete_cookie('refresh_token')
            return response
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response(data={'message': 'An error occurred during logout.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# UserManagement
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]