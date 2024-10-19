from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed,ValidationError

class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate(self, data):
        username = data.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Username already exists.'})  

        return data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            refresh = RefreshToken(data['refresh'])
            token_data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            user = self.user
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'firstname': user.first_name,
                'lastname': user.last_name,
                'phone_number': user.phone_number,
                'address': user.address,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined,
            }
            return {
                'token': token_data,
                'user': user_data
            }
            
        except AuthenticationFailed as exc:
            raise ValidationError({'detail': str(exc)}, code='authentication_failed')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        exclude = ["last_login"]

        read_only_fields=['user_permissions','groups']
