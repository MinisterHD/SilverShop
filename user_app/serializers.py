from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError
from django.utils import timezone

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)

    def validate_phone_number(self, value):
        
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError("Enter a valid 11-digit phone number.")
        return value

class CheckOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=11)
    otp = serializers.CharField(max_length=6, required=False)

    def validate(self, data):
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        if not phone_number:
            raise serializers.ValidationError({'phone_number': 'Phone number is required.'})

        if otp:
            try:
                user = User.objects.get(phone_number=phone_number)
                if user.otp != otp or user.otp_expiration <= timezone.now():
                    raise serializers.ValidationError({'otp': 'Invalid or expired OTP.'})
            except User.DoesNotExist:
                raise serializers.ValidationError({'phone_number': 'User does not exist.'})

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["last_login"]
        read_only_fields = ['user_permissions', 'groups']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'address', 'email']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.address = validated_data.get('address', instance.address)
        instance.email = validated_data.get('email', instance.email)

        if instance.first_name and instance.last_name and instance.address and instance.email:
            instance.is_completed = True
        else:
            instance.is_completed = False

        instance.save()
        return instance