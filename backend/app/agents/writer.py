from typing import Any

from app.agents.base import BaseAgent
from app.agents.context import WorkflowContext
from app.errors import InvalidRequestError
from app.schemas.draft import DraftOutput


class WriterAgent(BaseAgent):
    name = "writer"
    output_model = DraftOutput

    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        if context.persona is None or context.outline is None:
            raise InvalidRequestError("persona and outline results are required")
        return {
            "article": context.article.model_dump(),
            "persona": context.persona.model_dump(),
            "outline": context.outline.model_dump(),
        }
