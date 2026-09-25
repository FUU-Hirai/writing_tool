from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.models.article import Article
from app.schemas.article import ArticleCreate
from app.status import ArticleStatus


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, data: ArticleCreate) -> Article:
        now = utcnow()
        article = Article(
            title=data.theme[:500],
            theme=data.theme,
            keyword=data.keyword,
            media=data.media,
            target_audience=data.target_audience,
            purpose=data.purpose,
            target_length=data.target_length,
            tone=data.tone,
            status=ArticleStatus.DRAFT,
            final_content=None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def list(self) -> list[Article]:
        result = await self.session.execute(select(Article).order_by(Article.created_at.desc(), Article.id.desc()))
        return list(result.scalars().all())

    async def get(self, article_id: int) -> Article | None:
        return await self.session.get(Article, article_id)

    async def mark_processing_if_idle(self, article_id: int) -> bool:
        result = await self.session.execute(
            update(Article)
            .where(Article.id == article_id, Article.status != ArticleStatus.PROCESSING)
            .values(status=ArticleStatus.PROCESSING, updated_at=utcnow())
        )
        return result.rowcount == 1
