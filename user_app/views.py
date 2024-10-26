from .models import User
from .serializers import UserSignUpSerializer, OTPLoginSerializer, UserSerializer
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import JSONParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
import logging
from .permissions import IsOwnerOrAdmin
from rest_framework.generics import CreateAPIView
from django.conf import settings
from django.db.models import Q
from django.utils import timezone  
from datetime import datetime, timedelta
from .utils import generate_otp, send_otp_via_sms

logger = logging.getLogger(__name__)

class SignUpView(CreateAPIView):
    serializer_class = UserSignUpSerializer
    parser_classes = [JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            phone_number = serializer.validated_data['phone_number']
            if User.objects.filter(phone_number=phone_number).exists():
                raise ValidationError({'phone_number': _('Phone number already exists.')})

            user = serializer.save()

       
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            response_data = {
                'user': serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': access_token,
                }
            }

          
            response = Response(data=response_data, status=status.HTTP_201_CREATED)
            access_token_expiration = datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            refresh_token_expiration = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

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


class OTPLoginView(APIView):
    def post(self, request):
        serializer = OTPLoginSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data.get('otp')

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                logger.error(f"User with phone number {phone_number} does not exist.")
                return Response({'error': 'User with this phone number does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            if otp:
                if user.otp == otp and user.otp_expiration > timezone.now():  
              
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)

                    response_data = {
                        'user': {
                            'id': user.id,
                            'phone_number': user.phone_number,
                            'email': user.email,
                        },
                        'tokens': {
                            'refresh': str(refresh),
                            'access': access_token,
                        }
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Invalid or expired OTP for user with phone number {phone_number}.")
                    return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp = generate_otp()
                user.otp = otp
                user.otp_expiration = timezone.now() + timedelta(minutes=10)  
                user.save()
                send_otp_via_sms(phone_number, otp)
                return Response({'message': 'OTP sent to your phone number.'}, status=status.HTTP_200_OK)
        logger.error(f"OTP login validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        try:
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            response = Response(data={'message': f'Bye {request.user.phone_number}!'}, status=status.HTTP_204_NO_CONTENT)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.delete_cookie('refresh_token')
            return response
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response(data={'message': 'An error occurred during logout.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]
    parser_classes = [JSONParser]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        try:
            obj = super().get_object()
            if self.request.user.is_staff or obj.id == self.request.user.id:
                return obj
            raise PermissionDenied("You do not have permission to access this user's profile.")
        except PermissionDenied as e:
            logger.error(f"Permission denied: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            raise NotFound(detail=str(e))

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_users(self, request):
        queryset = self.get_queryset()
        is_staff = request.query_params.get('is_staff', None)
        if is_staff is not None:
            is_staff = is_staff.lower()
            if is_staff == 'true':
                queryset = queryset.filter(is_staff=True)
            elif is_staff == 'false':
                queryset = queryset.filter(is_staff=False)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  
        serializer = UserSerializer(user)  
        return Response(serializer.data)