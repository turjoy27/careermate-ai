from django.urls import path
from .views import (
    ConversationDetailAPIView,
    ConversationListCreateAPIView,
    MessageListCreateAPIView,
)

urlpatterns = [
    path('conversations/', ConversationListCreateAPIView.as_view(), name='api-chat-conversations'),
    path('conversations/<int:pk>/', ConversationDetailAPIView.as_view(), name='api-chat-conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', MessageListCreateAPIView.as_view(), name='api-chat-messages'),
]
