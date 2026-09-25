from dataclasses import dataclass

from app.schemas.article import ArticleInput
from app.schemas.draft import DraftOutput
from app.schemas.outline import OutlineOutput
from app.schemas.persona import PersonaOutput


@dataclass
class WorkflowContext:
    article: ArticleInput
    persona: PersonaOutput | None = None
    outline: OutlineOutput | None = None
    draft: DraftOutput | None = None
