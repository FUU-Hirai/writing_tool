from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.article_service import ArticleService


def get_article_service(session: AsyncSession = Depends(get_session)) -> ArticleService:
    return ArticleService(session)
