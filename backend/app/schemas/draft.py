from pydantic import BaseModel, Field


class DraftOutput(BaseModel):
    title: str
    content_markdown: str = Field(description="Markdown の記事本文")
