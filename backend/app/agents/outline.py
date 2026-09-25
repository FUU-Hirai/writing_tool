from typing import Any

from app.agents.base import BaseAgent
from app.agents.context import WorkflowContext
from app.errors import InvalidRequestError
from app.schemas.outline import OutlineOutput


class OutlineAgent(BaseAgent):
    name = "outline"
    output_model = OutlineOutput

    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        if context.persona is None:
            raise InvalidRequestError("persona result is required")
        return {
            "article": context.article.model_dump(),
            "persona": context.persona.model_dump(),
        }
