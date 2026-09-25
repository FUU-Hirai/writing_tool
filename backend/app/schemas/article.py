from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    theme: str = Field(min_length=1, max_length=2000)
    keyword: str = Field(min_length=1, max_length=255)
    media: str = Field(min_length=1, max_length=100)
    target_audience: str = Field(min_length=1, max_length=2000)
    purpose: str = Field(min_length=1, max_length=2000)
    target_length: int = Field(ge=300, le=20000)
    tone: str = Field(min_length=1, max_length=1000)


class ArticleInput(BaseModel):
    theme: str
    keyword: str
    media: str
    target_audience: str
    purpose: str
    target_length: int
    tone: str


class ArticleAccepted(BaseModel):
    id: int
    status: str


class ArticleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    theme: str
    status: str
    created_at: datetime


class ArticleDetail(ArticleSummary):
    keyword: str
    media: str
    target_audience: str
    purpose: str
    target_length: int
    tone: str
    final_content: str | None
    updated_at: datetime


class ArticleVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    version: int
    content: str
    created_at: datetime
