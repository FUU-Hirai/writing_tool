from pydantic import BaseModel, Field


class OutlineSection(BaseModel):
    heading: str
    purpose: str
    points: list[str]


class OutlineOutput(BaseModel):
    title: str = Field(description="記事タイトル")
    sections: list[OutlineSection]
