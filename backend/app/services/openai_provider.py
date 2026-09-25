from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

from app.errors import (
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMTimeoutError,
    StructuredOutputError,
)
from app.services.llm_service import ProviderResult


class OpenAIProvider:
    def __init__(self, api_key: str, timeout: float) -> None:
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key or "missing", timeout=timeout)

    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        response_model: type[BaseModel],
        max_tokens: int,
    ) -> ProviderResult:
        if not self.api_key:
            raise LLMInvalidResponseError("OpenAI credential is not configured")
        try:
            completion = await self.client.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=response_model,
                max_tokens=max_tokens,
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError("OpenAI API timeout") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError("OpenAI API rate limit") from exc
        except (APIError, ValidationError) as exc:
            raise LLMInvalidResponseError("OpenAI API error") from exc

        choice = completion.choices[0].message
        if getattr(choice, "refusal", None):
            raise LLMInvalidResponseError("OpenAI API refusal")
        if choice.parsed is None:
            raise StructuredOutputError("Structured output parse error")
        usage = completion.usage
        return ProviderResult(
            output=choice.parsed,
            model=completion.model or model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
