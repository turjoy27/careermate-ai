from django.db import models
from apps.accounts.models import UserProfile


class ChatConversation(models.Model):
    """A persistent conversation session between a user and CareerMate AI."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='chat_conversations'
    )
    title = models.CharField(max_length=200, default='New Career Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Chat Conversation'
        verbose_name_plural = 'Chat Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.profile.user.email})"


class ChatMessage(models.Model):
    """Individual message in a conversation thread."""

    SENDER_CHOICES = (
        ('user', 'User'),
        ('assistant', 'CareerMate AI'),
    )

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.message_text[:40]}..."
