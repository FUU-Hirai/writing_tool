import json
import time
from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.services.prompt_loader import load_prompt

T = TypeVar("T", bound=BaseModel)


@dataclass
class ProviderResult:
    output: BaseModel
    model: str
    input_tokens: int
    output_tokens: int


@dataclass
class LLMResult:
    output: BaseModel
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    execution_time_ms: int


class LLMProvider(Protocol):
    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        response_model: type[BaseModel],
        max_tokens: int,
    ) -> ProviderResult:
        pass


class LLMService:
    def __init__(self, provider: LLMProvider, model: str, max_tokens: int) -> None:
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens

    async def generate(
        self,
        *,
        agent_name: str,
        prompt_version: str,
        user_payload: dict,
        response_model: type[T],
    ) -> LLMResult:
        system_prompt = load_prompt(agent_name, prompt_version)
        user_content = (
            "以下のJSONを入力として、システムプロンプトの役割だけを実行してください。\n"
            + json.dumps(user_payload, ensure_ascii=False, indent=2)
        )
        started = time.perf_counter()
        result = await self.provider.complete(
            model=self.model,
            system_prompt=system_prompt,
            user_content=user_content,
            response_model=response_model,
            max_tokens=self.max_tokens,
        )
        elapsed = int((time.perf_counter() - started) * 1000)
        return LLMResult(
            output=result.output,
            model=result.model,
            prompt_version=prompt_version,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            execution_time_ms=elapsed,
        )
