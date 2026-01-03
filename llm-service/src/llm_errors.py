"""Custom exception classes for LLM service errors."""


class LLMError(Exception):
    """Base class for all LLM-related errors."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limit is exceeded."""

    pass


class LLMUnavailableError(LLMError):
    """Raised when LLM service is temporarily unavailable."""

    pass
