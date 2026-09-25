from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.agents.context import WorkflowContext
from app.services.llm_service import LLMService
from app.services.prompt_loader import active_prompt_version


@dataclass
class AgentResult:
    output: BaseModel
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    execution_time_ms: int


class BaseAgent(ABC):
    name: str
    output_model: type[BaseModel]

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    @property
    def prompt_version(self) -> str:
        return active_prompt_version(self.name)

    @abstractmethod
    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        pass

    async def run(self, context: WorkflowContext) -> AgentResult:
        payload = self.build_input(context)
        result = await self.llm.generate(
            agent_name=self.name,
            prompt_version=self.prompt_version,
            user_payload=payload,
            response_model=self.output_model,
        )
        return AgentResult(
            output=result.output,
            model=result.model,
            prompt_version=result.prompt_version,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            execution_time_ms=result.execution_time_ms,
        )
