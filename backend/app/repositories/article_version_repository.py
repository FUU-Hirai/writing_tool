from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.models.article_version import ArticleVersion


class ArticleVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, article_id: int, content: str) -> ArticleVersion:
        current = await self.session.scalar(
            select(func.max(ArticleVersion.version)).where(ArticleVersion.article_id == article_id)
        )
        version = ArticleVersion(
            article_id=article_id,
            version=(current or 0) + 1,
            content=content,
            created_at=utcnow(),
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def list_for_article(self, article_id: int) -> list[ArticleVersion]:
        result = await self.session.execute(
            select(ArticleVersion)
            .where(ArticleVersion.article_id == article_id)
            .order_by(ArticleVersion.version.desc())
        )
        return list(result.scalars().all())
