import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from apps.ai_services.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIServiceError,
    AIUnavailableError,
)
from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatMessageSerializer
from .services import ChatService


# ==============================================================================
# Web UI Views
# ==============================================================================

@method_decorator(login_required(login_url='accounts-login'), name='dispatch')
class ChatPortalView(View):
    """Main interactive chat interface with conversation history and active session."""
    template_name = 'chat/index.html'

    def get(self, request, conversation_id=None):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        try:
            active_conversation = ChatService.get_or_create_active_conversation(profile, conversation_id)
        except ChatConversation.DoesNotExist:
            return redirect('chat-portal')

        conversations = profile.chat_conversations.all()
        chat_messages = active_conversation.messages.all()

        starter_prompts = [
            "How can I tailor my CV for a Python Backend role in Dhaka?",
            "What technical questions should I expect in a junior software interview?",
            "How is the salary and career progression for a software engineer in Bangladesh?",
            "What high-impact project should I build to stand out to local tech recruiters?",
        ]

        return render(request, self.template_name, {
            'profile': profile,
            'conversations': conversations,
            'active_conversation': active_conversation,
            'chat_messages': chat_messages,
            'starter_prompts': starter_prompts,
        })


@login_required(login_url='accounts-login')
def new_chat(request):
    """Starts a new conversation thread and redirects to it."""
    profile = get_object_or_404(UserProfile, user=request.user)
    conversation = ChatService.create_new_conversation(profile)
    return redirect('chat-conversation', conversation_id=conversation.id)


@login_required(login_url='accounts-login')
def delete_chat(request, pk):
    """Deletes a conversation owned by the authenticated user."""
    profile = get_object_or_404(UserProfile, user=request.user)
    conversation = get_object_or_404(ChatConversation, pk=pk, profile=profile)
    conversation.delete()
    messages.info(request, "Conversation deleted.")
    return redirect('chat-portal')


@login_required(login_url='accounts-login')
@require_POST
def send_chat_message_ajax(request, conversation_id):
    """AJAX handler for sending messages and receiving AI replies."""
    profile = get_object_or_404(UserProfile, user=request.user)
    conversation = get_object_or_404(ChatConversation, pk=conversation_id, profile=profile)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        text = data.get('message', '').strip()

        user_msg, assistant_msg = ChatService.send_user_message(conversation, text)

        return JsonResponse({
            'status': 'success',
            'user_message': {
                'id': user_msg.id,
                'sender': user_msg.sender,
                'message_text': user_msg.message_text,
                'created_at': user_msg.created_at.strftime('%I:%M %p'),
            },
            'assistant_message': {
                'id': assistant_msg.id,
                'sender': assistant_msg.sender,
                'message_text': assistant_msg.message_text,
                'created_at': assistant_msg.created_at.strftime('%I:%M %p'),
            },
            'conversation_title': conversation.title,
        })
    except ValueError as val_err:
        return JsonResponse({'status': 'error', 'message': str(val_err)}, status=400)
    except AIConfigurationError as conf_err:
        return JsonResponse({'status': 'error', 'message': str(conf_err)}, status=503)
    except AIRateLimitError as rate_err:
        return JsonResponse({'status': 'error', 'message': str(rate_err)}, status=429)
    except (AIServiceError, AIUnavailableError) as ai_err:
        return JsonResponse({'status': 'error', 'message': str(ai_err)}, status=502)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Unexpected server error: {str(e)}"}, status=500)


# ==============================================================================
# REST API Endpoints
# ==============================================================================

class ConversationListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        conversations = profile.chat_conversations.all()
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        title = request.data.get('title', 'New Career Consultation')
        conversation = ChatService.create_new_conversation(profile, title=title)
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        conversation = get_object_or_404(ChatConversation, pk=pk, profile=profile)
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        conversation = get_object_or_404(ChatConversation, pk=pk, profile=profile)
        conversation.delete()
        return Response({'message': 'Conversation deleted.'}, status=status.HTTP_204_NO_CONTENT)


class MessageListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        conversation = get_object_or_404(ChatConversation, pk=conversation_id, profile=profile)
        messages_qs = conversation.messages.all()
        serializer = ChatMessageSerializer(messages_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        profile = get_object_or_404(UserProfile, user=request.user)
        conversation = get_object_or_404(ChatConversation, pk=conversation_id, profile=profile)

        text = request.data.get('message', '').strip()
        try:
            user_msg, assistant_msg = ChatService.send_user_message(conversation, text)
            return Response({
                'user_message': ChatMessageSerializer(user_msg).data,
                'assistant_message': ChatMessageSerializer(assistant_msg).data,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AIConfigurationError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIRateLimitError as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (AIServiceError, AIUnavailableError) as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
