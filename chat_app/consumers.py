import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from channels.db import database_sync_to_async
import time
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    from collections import defaultdict
    
    connection_timestamps = defaultdict(list)

    async def connect(self):
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        logger.info("WebSocket connection attempt")

        # Rate limiting
        user_ip = self.scope['client'][0]
        current_time = time.time()
        self.connection_timestamps[user_ip] = [
            timestamp for timestamp in self.connection_timestamps[user_ip]
            if current_time - timestamp < 60  # Keep only the timestamps within the last minute
        ]

        if len(self.connection_timestamps[user_ip]) >= 10:
            logger.error("Rate limit exceeded")
            await self.close()
            raise DenyConnection("Rate limit exceeded")

        self.connection_timestamps[user_ip].append(current_time)

        # Token validation
        query_string = self.scope['query_string'].decode()
        logger.info(f"Query string: {query_string}")
        token = query_string.split('=')[1] if '=' in query_string else None

        if not token:
            logger.error("Token not found in query string")
            await self.close()
            raise DenyConnection("Token not found in query string")

        try:
            untoken = UntypedToken(token)
            user_id = untoken['user_id']
            self.scope['user'] = await self.get_user(user_id)
            logger.info(f"Token valid, user_id: {user_id}")
        except (InvalidToken, TokenError) as e:
            logger.error(f"Token error: {e}")
            await self.close()
            raise DenyConnection(f"Token error: {e}")

        # User authentication
        if not self.scope["user"] or not self.scope["user"].is_authenticated:
            logger.error("User is not authenticated")
            await self.close()
            raise DenyConnection("User is not authenticated")

        # Room setup
        other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        self.room_name = f'chat_{min(user_id, other_user_id)}_{max(user_id, other_user_id)}'
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()
        logger.info("WebSocket connection accepted")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info("WebSocket connection closed")

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']
        other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        receiver = await self.get_user(other_user_id)

        if receiver:

            await self.save_message(sender, receiver, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_channel_name': self.channel_name
                }
            )

    async def chat_message(self, event):
        message = event['message']
        sender_channel_name = event['sender_channel_name']
        if self.channel_name != sender_channel_name:
            logger.info(f"Broadcasting message: {message}")
            await self.send(text_data=json.dumps({
                'message': message
            }))

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, sender, receiver, message):
        from .models import Message
        Message.objects.create(sender=sender, receiver=receiver, content=message)