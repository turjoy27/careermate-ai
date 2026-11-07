from rest_framework import serializers
from .models import ChatConversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message_text', 'created_at']


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = ChatConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'messages']
