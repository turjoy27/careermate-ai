from django.urls import path
from .views import (
    ChatPortalView,
    delete_chat,
    new_chat,
    send_chat_message_ajax,
)

urlpatterns = [
    path('', ChatPortalView.as_view(), name='chat-portal'),
    path('new/', new_chat, name='chat-new'),
    path('<int:conversation_id>/', ChatPortalView.as_view(), name='chat-conversation'),
    path('<int:pk>/delete/', delete_chat, name='chat-delete'),
    path('<int:conversation_id>/send/', send_chat_message_ajax, name='chat-send-ajax'),
]
