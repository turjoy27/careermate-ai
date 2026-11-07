import json
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Education, UserProfile, UserSkill
from apps.ai_services.exceptions import AIRateLimitError, AIServiceError
from apps.chat.models import ChatConversation, ChatMessage
from apps.chat.services import ChatService

User = get_user_model()


class ChatModelAndServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='chatuser@example.com',
            password='Password123!',
            first_name='Tasnim',
            last_name='Zara'
        )
        self.profile = self.user.profile
        self.profile.headline = 'Junior Frontend Engineer'
        self.profile.target_career = 'React Native Mobile Developer'
        self.profile.city = 'Dhaka'
        self.profile.save()

        UserSkill.objects.create(profile=self.profile, skill_name='React')
        UserSkill.objects.create(profile=self.profile, skill_name='JavaScript')

    def test_create_new_conversation_seeds_greeting(self):
        conv = ChatService.create_new_conversation(self.profile)
        self.assertEqual(conv.profile, self.profile)
        self.assertEqual(conv.messages.count(), 1)

        first_msg = conv.messages.first()
        self.assertEqual(first_msg.sender, 'assistant')
        self.assertIn('CareerMate AI', first_msg.message_text)

    def test_get_or_create_active_conversation(self):
        # Initial call creates one
        conv1 = ChatService.get_or_create_active_conversation(self.profile)
        self.assertIsNotNone(conv1.id)

        # Second call returns existing
        conv2 = ChatService.get_or_create_active_conversation(self.profile)
        self.assertEqual(conv1.id, conv2.id)

    def test_send_user_message_success(self):
        conv = ChatService.create_new_conversation(self.profile)

        mock_ai = MagicMock()
        mock_ai.send_chat_message.return_value = (
            "For React Native in Dhaka, focus on component lifecycles, Redux, and offline sync."
        )

        user_msg, assistant_msg = ChatService.send_user_message(
            conv,
            "What should I study for React Native in Dhaka?",
            ai_service=mock_ai
        )

        self.assertEqual(user_msg.sender, 'user')
        self.assertEqual(user_msg.message_text, "What should I study for React Native in Dhaka?")
        self.assertEqual(assistant_msg.sender, 'assistant')
        self.assertIn("React Native in Dhaka", assistant_msg.message_text)

        # Title auto-updated
        conv.refresh_from_db()
        self.assertNotEqual(conv.title, "New Career Consultation")

        # History checked
        self.assertEqual(conv.messages.count(), 3)  # Greeting + User + Assistant

    def test_empty_message_raises_value_error(self):
        conv = ChatService.create_new_conversation(self.profile)
        with self.assertRaises(ValueError):
            ChatService.send_user_message(conv, "   ")

    def test_oversized_message_raises_value_error(self):
        conv = ChatService.create_new_conversation(self.profile)
        oversized = "a" * 2001
        with self.assertRaises(ValueError):
            ChatService.send_user_message(conv, oversized)

    def test_rate_limiting_exceeded(self):
        conv = ChatService.create_new_conversation(self.profile)

        # Seed 15 messages in the current window
        for i in range(ChatService.MAX_MESSAGES_PER_WINDOW):
            ChatMessage.objects.create(
                conversation=conv,
                sender='user',
                message_text=f'Message {i}'
            )

        with self.assertRaises(AIServiceError):
            ChatService.send_user_message(conv, "One more message should exceed limit")


class ChatOwnershipAndAccessTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email='user_a@example.com', password='Password123!')
        self.user_b = User.objects.create_user(email='user_b@example.com', password='Password123!')

        self.conv_a = ChatService.create_new_conversation(self.user_a.profile, title="User A Private Chat")
        self.conv_b = ChatService.create_new_conversation(self.user_b.profile, title="User B Private Chat")

        self.client_a = Client()
        self.client_a.login(email='user_a@example.com', password='Password123!')

    def test_unauthenticated_access_redirects(self):
        anon_client = Client()
        response = anon_client.get(reverse('chat-portal'))
        self.assertEqual(response.status_code, 302)

    def test_user_cannot_access_other_users_conversation(self):
        # User A tries to open User B's conversation
        url = reverse('chat-conversation', kwargs={'conversation_id': self.conv_b.id})
        response = self.client_a.get(url, follow=True)
        # Should redirect back to their own chat portal
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User B Private Chat")

    def test_user_cannot_send_message_to_other_users_conversation(self):
        url = reverse('chat-send-ajax', kwargs={'conversation_id': self.conv_b.id})
        response = self.client_a.post(
            url,
            data=json.dumps({'message': 'Intruder message'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class ChatWebViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='portaluser@example.com',
            password='Password123!',
            first_name='Salma'
        )
        self.profile = self.user.profile
        self.client.login(email='portaluser@example.com', password='Password123!')

    def test_chat_portal_get_and_new_chat(self):
        response = self.client.get(reverse('chat-portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Career Advisor Chat')

        # New chat
        new_res = self.client.get(reverse('chat-new'), follow=True)
        self.assertEqual(new_res.status_code, 200)
        self.assertEqual(self.profile.chat_conversations.count(), 2)

    @patch('apps.chat.services.GeminiService')
    def test_send_chat_message_ajax_endpoint(self, mock_gemini_class):
        mock_instance = MagicMock()
        mock_instance.send_chat_message.return_value = "Great question! Here are 3 tips for your career."
        mock_gemini_class.return_value = mock_instance

        conv = ChatService.create_new_conversation(self.profile)
        url = reverse('chat-send-ajax', kwargs={'conversation_id': conv.id})

        response = self.client.post(
            url,
            data=json.dumps({'message': 'How do I start learning Django?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Here are 3 tips', data['assistant_message']['message_text'])


class ChatAPITests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email='chat_api@example.com',
            password='Password123!',
            first_name='Zubair'
        )
        self.profile = self.user.profile
        self.api_client.force_authenticate(user=self.user)

    def test_api_conversations_list_and_create(self):
        res = self.api_client.post(reverse('api-chat-conversations'), {'title': 'API Discussion'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        conv_id = res.data['id']

        list_res = self.api_client.get(reverse('api-chat-conversations'))
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    @patch('apps.chat.services.GeminiService')
    def test_api_post_message(self, mock_gemini_class):
        mock_instance = MagicMock()
        mock_instance.send_chat_message.return_value = "AI API Response text."
        mock_gemini_class.return_value = mock_instance

        conv = ChatService.create_new_conversation(self.profile)
        url = reverse('api-chat-messages', kwargs={'conversation_id': conv.id})

        response = self.api_client.post(url, {'message': 'Tell me about salary in BD'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['assistant_message']['message_text'], "AI API Response text.")
