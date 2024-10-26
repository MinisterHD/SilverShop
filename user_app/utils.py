import random
from kavenegar import *
from django.conf import settings

def generate_otp():
    
    return str(random.randint(100000, 999999))

def send_otp_via_sms(phone_number, otp):
    
    try:
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        params = {
            'sender': '',  
            'receptor': phone_number,
            'message': f"Your OTP is {otp}"
        }
        response = api.sms_send(params)
        return response
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)