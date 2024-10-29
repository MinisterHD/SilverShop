from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from order_app.serializers import CartSerializer
from order_app.models import Cart
import requests
import json

#? sandbox merchant 
sandbox = 'sandbox' if settings.SANDBOX else 'www'

ZP_API_REQUEST = f"https://{sandbox}.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
ZP_API_VERIFY = f"https://{sandbox}.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
ZP_API_STARTPAY = f"https://{sandbox}.zarinpal.com/pg/StartPay/"

description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"  # Required
phone = 'YOUR_PHONE_NUMBER'  # Optional
# Important: need to edit for real server.
CallbackURL = 'http://127.0.0.1:8080/verify/'

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    cart_serializer = CartSerializer(cart)
    amount = cart_serializer.data['total_price']

    if amount <= 0:
        return Response({"detail": "Your cart is empty or has invalid items."}, status=status.HTTP_400_BAD_REQUEST)

    response = send_request(request)
    return Response(response)

def send_request(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    cart_serializer = CartSerializer(cart)
    amount = cart_serializer.data['total_price']

    data = {
        "MerchantID": settings.MERCHANT,
        "Amount": amount,
        "Description": description,
        "Phone": phone,
        "CallbackURL": CallbackURL,
    }
    data = json.dumps(data)
    headers = {'content-type': 'application/json', 'content-length': str(len(data))}
    try:
        response = requests.post(ZP_API_REQUEST, data=data, headers=headers, timeout=10)
        if response.status_code == 200:
            response = response.json()
            if response['Status'] == 100:
                return {'status': True, 'url': ZP_API_STARTPAY + str(response['Authority']), 'authority': response['Authority']}
            else:
                return {'status': False, 'code': str(response['Status'])}
        return {'status': False, 'code': 'error'}
    except requests.exceptions.Timeout:
        return {'status': False, 'code': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'status': False, 'code': 'connection error'}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify(request):
    authority = request.data.get('authority')
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    cart_serializer = CartSerializer(cart)
    amount = cart_serializer.data['total_price']

    data = {
        "MerchantID": settings.MERCHANT,
        "Amount": amount,
        "Authority": authority,
    }
    data = json.dumps(data)
    headers = {'content-type': 'application/json', 'content-length': str(len(data))}
    response = requests.post(ZP_API_VERIFY, data=data, headers=headers)
    if response.status_code == 200:
        response = response.json()
        if response['Status'] == 100:
            return Response({'status': True, 'RefID': response['RefID']})
        else:
            return Response({'status': False, 'code': str(response['Status'])})
    return Response({'status': False, 'code': 'error'})