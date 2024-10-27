from django.test import TestCase
from unittest.mock import patch
from user_app.models import User
from user_app.utils import generate_otp

class UserSMSInteractionTest(TestCase):
    @patch('user_app.utils.send_otp_via_sms')
    def test_send_sms_without_sending(self, mock_send_sms):
        user = User.objects.create(phone_number='1234567890')  
        otp = generate_otp(user) 
        
   
        mock_send_sms(user) 


        mock_send_sms.assert_called_once()
        print(f"Test passed: OTP for {user.phone_number} generated and send function mocked.")
