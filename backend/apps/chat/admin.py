from django.contrib import admin
from .models import ChatConversation, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'message_text', 'created_at')


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'profile', 'created_at', 'updated_at')
    search_fields = ('title', 'profile__user__email')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('message_text', 'conversation__profile__user__email')
