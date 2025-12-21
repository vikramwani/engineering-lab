class LLMError(Exception):
    """Base class for all LLM-related errors."""
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMUnavailableError(LLMError):
    pass
