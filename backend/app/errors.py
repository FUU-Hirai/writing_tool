class AppError(Exception):
    pass


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class InvalidRequestError(AppError):
    pass


class LLMError(AppError):
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMInvalidResponseError(LLMError):
    pass


class StructuredOutputError(LLMError):
    pass


def public_error_message(exc: Exception) -> str:
    if isinstance(exc, LLMTimeoutError):
        return "OpenAI API timeout"
    if isinstance(exc, LLMRateLimitError):
        return "OpenAI API rate limit"
    if isinstance(exc, StructuredOutputError):
        return "Structured output parse error"
    if isinstance(exc, LLMError):
        text = str(exc)
        if _looks_sensitive(text):
            return "Agent error"
        return text[:500] or "OpenAI API error"
    if exc.__class__.__name__.endswith("SQLAlchemyError") or exc.__class__.__module__.startswith("sqlalchemy"):
        return "DB error"
    text = f"{exc.__class__.__name__}: {exc}"
    if _looks_sensitive(text):
        return "Agent error"
    return text[:500]


def _looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return "sk-" in text or "api_key" in lowered or "authorization" in lowered
