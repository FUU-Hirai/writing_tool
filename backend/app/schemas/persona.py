from typing import Literal

from pydantic import BaseModel, Field


class PersonaOutput(BaseModel):
    persona: str = Field(description="想定読者を一文で表したペルソナ")
    problems: list[str] = Field(description="読者が抱える課題")
    needs: list[str] = Field(description="読者が記事に求めていること")
    knowledge_level: Literal["beginner", "intermediate", "advanced"]
    desired_action: str = Field(description="記事を読んだ後に取ってほしい行動")
