from app.config import get_settings
from app.services.llm_service import LLMService
from app.services.openai_provider import OpenAIProvider


def default_llm_service() -> LLMService:
    settings = get_settings()
    provider = OpenAIProvider(settings.openai_api_key, settings.openai_timeout_seconds)
    return LLMService(provider, model=settings.openai_model, max_tokens=settings.openai_max_tokens)


class Container:
    def __init__(self) -> None:
        self.llm_service_factory = default_llm_service


container = Container()
