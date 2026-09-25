from typing import Any

from app.agents.base import BaseAgent
from app.agents.context import WorkflowContext
from app.schemas.persona import PersonaOutput


class PersonaAgent(BaseAgent):
    name = "persona"
    output_model = PersonaOutput

    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        return {"article": context.article.model_dump()}
