from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LogoutView, SignUpView, LoginView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]