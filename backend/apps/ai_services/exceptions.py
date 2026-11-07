"""
Custom exceptions for CareerMate AI services.
"""


class AIServiceError(Exception):
    """Base exception for all AI service operations."""
    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        self.code = code or "AI_ERROR"
        self.details = details or {}


class AIConfigurationError(AIServiceError):
    """Raised when the AI service is misconfigured (e.g. missing API key)."""
    def __init__(self, message="Gemini API credentials are not configured."):
        super().__init__(message, code="CONFIG_ERROR")


class AIRateLimitError(AIServiceError):
    """Raised when Gemini API quota or rate limit is exceeded."""
    def __init__(self, message="AI service rate limit exceeded. Please try again shortly."):
        super().__init__(message, code="RATE_LIMIT_ERROR")


class AIResponseValidationError(AIServiceError):
    """Raised when the AI model returns malformed JSON or invalid schema."""
    def __init__(self, message="Failed to parse structured output from AI model.", raw_response=None):
        super().__init__(message, code="VALIDATION_ERROR", details={"raw_response": raw_response})


class AIUnavailableError(AIServiceError):
    """Raised when the Gemini API is unreachable or returns a server error."""
    def __init__(self, message="Gemini AI service is temporarily unavailable."):
        super().__init__(message, code="SERVICE_UNAVAILABLE")
