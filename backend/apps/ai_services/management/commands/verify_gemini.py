import time
from django.core.management.base import BaseCommand
from apps.ai_services.client import GeminiService
from apps.ai_services.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIServiceError,
    AIUnavailableError,
)


class Command(BaseCommand):
    help = "Verifies Google Gemini API credentials, models connectivity, and response latency."

    def add_arguments(self, parser):
        parser.add_argument(
            '--prompt',
            type=str,
            default='Say "CareerMate AI is online and operational!" in exactly one sentence.',
            help='Prompt to test live generation.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Testing Google Gemini API integration for CareerMate AI..."))

        service = GeminiService()

        # Step 1: Check key configuration
        if not service.api_key or service.api_key.strip() in ("", "your_gemini_api_key_here"):
            self.stdout.write(self.style.ERROR("FAIL: GEMINI_API_KEY is not configured in environment variables or .env."))
            return

        masked_key = service.api_key[:6] + "..." + service.api_key[-4:] if len(service.api_key) > 10 else "***"
        self.stdout.write(f"Key configured: {masked_key}")
        self.stdout.write(f"Default model: {service.DEFAULT_MODEL}")

        # Step 2: Initialize Client & List Models
        try:
            client = service._get_client()
            self.stdout.write("Connecting to Google Gen AI Client...")
            start_time = time.time()
            models_list = [m.name for m in client.models.list()][:5]
            duration = round(time.time() - start_time, 2)
            self.stdout.write(self.style.SUCCESS(f"Connected successfully in {duration}s! Available models sample: {models_list}"))
        except AIConfigurationError as e:
            self.stdout.write(self.style.ERROR(f"Configuration Error: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection Failed: {e}"))
            return

        # Step 3: Test Content Generation
        test_prompt = options['prompt']
        self.stdout.write(f"Testing generate_content with prompt: \"{test_prompt}\"...")
        try:
            start_time = time.time()
            response = client.models.generate_content(
                model=service.DEFAULT_MODEL,
                contents=test_prompt
            )
            duration = round(time.time() - start_time, 2)
            reply = getattr(response, 'text', '').strip()
            self.stdout.write(self.style.SUCCESS(f"Success ({duration}s)! Response:\n\"{reply}\""))
            self.stdout.write(self.style.SUCCESS("All Gemini API integration checks PASSED."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Generation Failed: {e}"))
