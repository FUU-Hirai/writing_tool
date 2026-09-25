from typing import Any

from app.agents.base import BaseAgent
from app.agents.context import WorkflowContext
from app.errors import InvalidRequestError
from app.schemas.review import ReviewOutput


class ReviewAgent(BaseAgent):
    name = "review"
    output_model = ReviewOutput

    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        if context.draft is None:
            raise InvalidRequestError("draft is required")
        return {
            "article": context.article.model_dump(),
            "persona": context.persona.model_dump() if context.persona else None,
            "outline": context.outline.model_dump() if context.outline else None,
            "draft": context.draft.model_dump(),
        }
