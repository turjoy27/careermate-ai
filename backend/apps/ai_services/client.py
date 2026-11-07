"""
Centralized Gemini AI client service using the official Google Gen AI Python SDK.
"""

import json
import logging
import os
from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from .exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseValidationError,
    AIServiceError,
    AIUnavailableError,
)
from .prompts import (
    CAREER_RECOMMENDATION_SYSTEM_INSTRUCTION,
    CV_ENHANCE_SYSTEM_INSTRUCTION,
    INTERVIEW_SYSTEM_INSTRUCTION,
    ROADMAP_SYSTEM_INSTRUCTION,
    build_answer_evaluation_prompt,
    build_bullet_enhance_prompt,
    build_career_recommendation_prompt,
    build_chat_system_prompt,
    build_interview_questions_prompt,
    build_learning_roadmap_prompt,
    build_summary_prompt,
)
from .schemas import (
    AnswerEvaluationResponse,
    BulletPointEnhanceResponse,
    CareerRecommendationResponse,
    InterviewQuestionsResponse,
    LearningRoadmapResponse,
    SummaryEnhanceResponse,
)


logger = logging.getLogger(__name__)


class GeminiService:
    """Reusable enterprise service wrapping Google Gemini API."""

    DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    def __init__(self, api_key: str = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY', '')
        self._client = None

    def _get_client(self) -> genai.Client:
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here"):
            raise AIConfigurationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env configuration."
            )
        if self._client is None:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=30000)
            )
        return self._client

    def _execute_structured_request(
        self,
        system_instruction: str,
        prompt: str,
        response_schema: type[BaseModel],
        model: str = None,
        temperature: float = 0.3
    ):
        """Generic handler for structured outputs with standardized error handling and validation."""
        client = self._get_client()
        target_model = model or self.DEFAULT_MODEL

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
        )

        try:
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Gemini API call failed: %s", error_msg, exc_info=True)

            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise AIRateLimitError(
                    "Gemini API rate limit or quota exceeded. Please wait a minute and retry."
                ) from exc
            if "API_KEY_INVALID" in error_msg or "unauthorized" in error_msg.lower() or "forbidden" in error_msg.lower():
                raise AIConfigurationError(
                    "Provided Gemini API key is invalid or unauthorized."
                ) from exc
            if "unavailable" in error_msg.lower() or "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise AIUnavailableError(
                    "Google Gemini API is currently unreachable or timed out. Please check your network connection."
                ) from exc
            raise AIServiceError(f"Unexpected AI error: {error_msg}") from exc

        raw_text = getattr(response, 'text', None)
        if not raw_text:
            raise AIResponseValidationError("Received empty response from Gemini API.", raw_response="")

        try:
            clean_json = raw_text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            parsed_dict = json.loads(clean_json)
            validated = response_schema.model_validate(parsed_dict)
            return validated
        except (json.JSONDecodeError, ValidationError) as parse_err:
            logger.error("Failed to parse Gemini response: %s | Raw: %s", str(parse_err), raw_text)
            raise AIResponseValidationError(
                f"Failed to validate structured AI response: {str(parse_err)}",
                raw_response=raw_text
            ) from parse_err

    def generate_career_recommendations(
        self,
        profile_data: dict,
        preferences: dict = None,
        model: str = None
    ) -> CareerRecommendationResponse:
        """Sends candidate profile to Gemini and parses structured career recommendation options."""
        prompt = build_career_recommendation_prompt(profile_data, preferences)
        return self._execute_structured_request(
            system_instruction=CAREER_RECOMMENDATION_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=CareerRecommendationResponse,
            model=model,
            temperature=0.3
        )

    def generate_professional_summary(
        self,
        profile_data: dict,
        target_role: str = None,
        model: str = None
    ) -> SummaryEnhanceResponse:
        """Generates an impactful, truthful resume summary based on profile facts."""
        prompt = build_summary_prompt(profile_data, target_role)
        return self._execute_structured_request(
            system_instruction=CV_ENHANCE_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=SummaryEnhanceResponse,
            model=model,
            temperature=0.3
        )

    def enhance_bullet_point(
        self,
        draft_text: str,
        context: str = None,
        model: str = None
    ) -> BulletPointEnhanceResponse:
        """Polishes a work or project bullet point: improves action verbs and grammar."""
        prompt = build_bullet_enhance_prompt(draft_text, context)
        return self._execute_structured_request(
            system_instruction=CV_ENHANCE_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=BulletPointEnhanceResponse,
            model=model,
            temperature=0.2
        )

    def send_chat_message(
        self,
        conversation_history: list[dict],
        user_profile_data: dict = None,
        model: str = None
    ) -> str:
        """
        Sends conversation history to Gemini with candidate background context and returns assistant text.
        """
        client = self._get_client()
        target_model = model or self.DEFAULT_MODEL
        system_instruction = build_chat_system_prompt(user_profile_data)

        contents = []
        for msg in conversation_history:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            text = msg.get("text", "")
            if text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text)]
                    )
                )

        if not contents:
            raise ValueError("Conversation history cannot be empty.")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )

        try:
            response = client.models.generate_content(
                model=target_model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Gemini Chat call failed: %s", error_msg, exc_info=True)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise AIRateLimitError("CareerMate AI is experiencing high demand. Please wait a moment.") from exc
            if "API_KEY_INVALID" in error_msg or "unauthorized" in error_msg.lower():
                raise AIConfigurationError("Gemini API key is invalid or unauthorized.") from exc
            if "unavailable" in error_msg.lower() or "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise AIUnavailableError("Unable to reach Gemini AI service or request timed out. Check network.") from exc
            raise AIServiceError(f"AI response failed: {error_msg}") from exc

        reply = getattr(response, "text", None)
        if not reply:
            raise AIResponseValidationError("Gemini returned an empty reply.", raw_response="")
        return reply.strip()

    def generate_interview_questions(
        self,
        target_role: str,
        difficulty: str = "junior",
        question_type: str = "mixed",
        user_skills: list = None,
        count: int = 3,
        model: str = None
    ) -> InterviewQuestionsResponse:
        """Generates realistic technical and behavioral interview questions for a mock session."""
        prompt = build_interview_questions_prompt(
            target_role=target_role,
            difficulty=difficulty,
            question_type=question_type,
            user_skills=user_skills,
            count=count
        )
        return self._execute_structured_request(
            system_instruction=INTERVIEW_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=InterviewQuestionsResponse,
            model=model,
            temperature=0.4
        )

    def evaluate_interview_answer(
        self,
        question_text: str,
        user_answer: str,
        target_role: str = None,
        category: str = None,
        model: str = None
    ) -> AnswerEvaluationResponse:
        """Evaluates a candidate's response to an interview question with scores and structured feedback."""
        prompt = build_answer_evaluation_prompt(
            question_text=question_text,
            user_answer=user_answer,
            target_role=target_role,
            category=category
        )
        return self._execute_structured_request(
            system_instruction=INTERVIEW_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=AnswerEvaluationResponse,
            model=model,
            temperature=0.2
        )

    def generate_learning_roadmap(
        self,
        target_role: str,
        user_skills: list,
        experience_level: str = "beginner",
        weekly_hours: int = 10,
        model: str = None
    ) -> LearningRoadmapResponse:
        """Generates a personalized 3-stage learning roadmap (beginner, intermediate, advanced)."""
        prompt = build_learning_roadmap_prompt(
            target_role=target_role,
            user_skills=user_skills,
            experience_level=experience_level,
            weekly_hours=weekly_hours
        )
        return self._execute_structured_request(
            system_instruction=ROADMAP_SYSTEM_INSTRUCTION,
            prompt=prompt,
            response_schema=LearningRoadmapResponse,
            model=model,
            temperature=0.3
        )



