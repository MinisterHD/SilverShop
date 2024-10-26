from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError

class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number']

    def validate(self, data):
        return data

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        user, created = User.objects.get_or_create(phone_number=phone_number)
        return user

class OTPLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    otp = serializers.CharField(max_length=6, required=False)

    def validate(self, data):
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        if not phone_number:
            raise serializers.ValidationError({'phone_number': 'Phone number is required.'})

        if otp and not User.objects.filter(phone_number=phone_number, otp=otp).exists():
            raise serializers.ValidationError({'otp': 'Invalid OTP.'})

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["last_login"]
        read_only_fields = ['user_permissions', 'groups']