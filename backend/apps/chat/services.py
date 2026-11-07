"""
Service layer managing chatbot conversations, context injection, and AI communication.
"""

from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import UserProfile
from apps.ai_services.client import GeminiService
from apps.ai_services.exceptions import AIServiceError
from .models import ChatConversation, ChatMessage


class ChatService:
    """Orchestrates persistent career chat sessions with context injection."""

    MAX_MESSAGE_LENGTH = 2000
    RATE_LIMIT_WINDOW_SECONDS = 60
    MAX_MESSAGES_PER_WINDOW = 15

    @staticmethod
    def serialize_profile_context(profile: UserProfile) -> dict:
        """Serializes user background to anchor the AI's advice."""
        return {
            'full_name': profile.user.full_name,
            'role': profile.user.get_role_display(),
            'headline': profile.headline,
            'target_career': profile.target_career,
            'city': profile.city,
            'country': profile.country,
            'skills': [{'skill_name': s.skill_name} for s in profile.skills.all()],
            'educations': [
                {
                    'institution': e.institution,
                    'degree': e.degree,
                    'field_of_study': e.field_of_study,
                }
                for e in profile.educations.all()
            ],
        }

    @classmethod
    def create_new_conversation(cls, profile: UserProfile, title: str = "New Career Consultation") -> ChatConversation:
        """Initializes a new conversation and seeds it with an introductory message."""
        conversation = ChatConversation.objects.create(
            profile=profile,
            title=title
        )

        greeting = (
            f"Hello {profile.user.first_name or 'there'}! I am CareerMate AI, your dedicated career strategist "
            f"and technical mentor. Whether you want to explore career tracks, review your CV bullet points, "
            f"simulate technical interview questions, or understand salary trends in Bangladesh, I'm here to help. "
            f"What would you like to focus on today?"
        )

        ChatMessage.objects.create(
            conversation=conversation,
            sender='assistant',
            message_text=greeting
        )

        return conversation

    @classmethod
    def get_or_create_active_conversation(cls, profile: UserProfile, conversation_id: int = None) -> ChatConversation:
        """Fetches specified conversation or latest active conversation, creating one if none exist."""
        if conversation_id:
            return profile.chat_conversations.get(pk=conversation_id)

        latest = profile.chat_conversations.first()
        if latest:
            return latest

        return cls.create_new_conversation(profile)

    @classmethod
    def send_user_message(
        cls,
        conversation: ChatConversation,
        text: str,
        ai_service: GeminiService = None
    ) -> tuple[ChatMessage, ChatMessage]:
        """
        Validates message input, saves user message, calls Gemini with conversational context,
        and records the assistant reply.
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Message cannot be empty.")

        if len(clean_text) > cls.MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message exceeds maximum allowed length of {cls.MAX_MESSAGE_LENGTH} characters.")

        # Rate limiting: check recent messages in time window
        recent_threshold = timezone.now() - timedelta(seconds=cls.RATE_LIMIT_WINDOW_SECONDS)
        recent_count = ChatMessage.objects.filter(
            conversation__profile=conversation.profile,
            sender='user',
            created_at__gte=recent_threshold
        ).count()

        if recent_count >= cls.MAX_MESSAGES_PER_WINDOW:
            raise AIServiceError(
                f"You have sent too many messages recently. Please pause for a moment before sending another."
            )

        # Auto-update generic title on first user turn
        if conversation.title in ("New Career Consultation", "New Career Chat"):
            snippet = " ".join(clean_text.split()[:5])
            if snippet:
                conversation.title = snippet.capitalize()[:60]
                conversation.save(update_fields=['title'])

        # 1. Record User Message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            sender='user',
            message_text=clean_text
        )

        # 2. Build Multi-turn History (last 10 messages)
        history_records = conversation.messages.order_by('-created_at')[:10]
        history_records = reversed(list(history_records))

        history = [
            {
                'role': 'user' if m.sender == 'user' else 'model',
                'text': m.message_text
            }
            for m in history_records
        ]

        # 3. Call AI Service
        service = ai_service or GeminiService()
        profile_context = cls.serialize_profile_context(conversation.profile)
        assistant_reply_text = service.send_chat_message(history, user_profile_data=profile_context)

        # 4. Record Assistant Message
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            sender='assistant',
            message_text=assistant_reply_text
        )

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        return user_message, assistant_message
