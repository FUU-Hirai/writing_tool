from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, InvalidRequestError, NotFoundError
from app.models.agent_run import AgentRun
from app.models.article import Article
from app.models.article_version import ArticleVersion
from app.pipeline import AGENT_ORDER
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.article_version_repository import ArticleVersionRepository
from app.schemas.article import ArticleCreate
from app.status import ArticleStatus


class ArticleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.articles = ArticleRepository(session)
        self.runs = AgentRunRepository(session)
        self.versions = ArticleVersionRepository(session)

    async def create(self, data: ArticleCreate) -> Article:
        return await self.articles.add(data)

    async def list_articles(self) -> list[Article]:
        return await self.articles.list()

    async def get(self, article_id: int) -> Article:
        article = await self.articles.get(article_id)
        if article is None:
            raise NotFoundError(f"article {article_id} not found")
        return article

    async def list_runs(self, article_id: int) -> list[AgentRun]:
        await self.get(article_id)
        return await self.runs.list_for_article(article_id)

    async def list_versions(self, article_id: int) -> list[ArticleVersion]:
        await self.get(article_id)
        return await self.versions.list_for_article(article_id)

    async def begin_run(self, article_id: int, start_from: str | None) -> Article:
        article = await self.get(article_id)
        if article.status == ArticleStatus.PROCESSING:
            raise ConflictError("article is already processing")
        if start_from is not None:
            await self._ensure_prior_success(article_id, start_from)
        updated = await self.articles.mark_processing_if_idle(article_id)
        if not updated:
            raise ConflictError("article is already processing")
        await self.session.commit()
        self.session.expire_all()
        return await self.get(article_id)

    async def _ensure_prior_success(self, article_id: int, start_from: str) -> None:
        if start_from not in AGENT_ORDER:
            raise InvalidRequestError(f"unknown agent: {start_from}")
        start_index = AGENT_ORDER.index(start_from)
        for name in AGENT_ORDER[:start_index]:
            run = await self.runs.latest_success(article_id, name)
            if run is None:
                raise InvalidRequestError(f"{start_from} を再実行するには、先に {name} の成功結果が必要です")
