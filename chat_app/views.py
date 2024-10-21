import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

logger = logging.getLogger(__name__)

class ChatMessagePagination(PageNumberPagination):
    page_size = 10

class ChatMessageViewSet(viewsets.ModelViewSet):
    from .models import Message 
    queryset = Message.objects.all()  
    pagination_class = ChatMessagePagination

    def get_serializer_class(self):
        from .serializers import ChatMessageSerializer  
        if not hasattr(self, '_serializer_class'):
            self._serializer_class = ChatMessageSerializer
        return self._serializer_class

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        params = request.query_params

        sender = params.get('sender')
        receiver = params.get('receiver')
        timestamp = params.get('timestamp')

        if sender:
            queryset = queryset.filter(sender=sender)
        if receiver:
            queryset = queryset.filter(receiver=receiver)
        if timestamp:
            queryset = queryset.filter(timestamp=timestamp)

        page = self.paginate_queryset(queryset)
        serializer_class = self.get_serializer_class()
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        message.read = True
        message.save()
        return Response({'status': 'message marked as read'})