from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LogoutView, SendOTP, CheckOTP, UserProfileView,UserProfileUpdateView,AdminStatusViewSet
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'adminstatus', AdminStatusViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/send/', SendOTP.as_view(), name='send-otp'),
    path('auth/check/', CheckOTP.as_view(), name='check-otp'),  
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),
    
]