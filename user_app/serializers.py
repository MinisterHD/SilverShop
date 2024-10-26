from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError

class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number']  

    def validate(self, data):
        phone_number = data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({'phone_number': 'Phone number already exists.'})
        return data

    def create(self, validated_data):
        return super().create(validated_data)

class OTPLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    otp = serializers.CharField(max_length=6, required=False)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["last_login"]
        read_only_fields = ['user_permissions', 'groups']