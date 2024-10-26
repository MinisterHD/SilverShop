import random
from kavenegar import *
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def generate_otp(user):
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_expiration = timezone.now() + timedelta(minutes=10)
    user.save()
    return otp

def send_otp_via_sms(user):
    otp = generate_otp(user)
    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'sender': '',  
            'receptor': user.phone_number,
            'message': f"Your OTP is {otp}"
        }
        response = api.sms_send(params)
        return response
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)