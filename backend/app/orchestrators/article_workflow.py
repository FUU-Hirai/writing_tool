import logging
import time

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import WorkflowContext
from app.clock import utcnow
from app.config import get_settings
from app.errors import InvalidRequestError, NotFoundError, public_error_message
from app.models.article import Article
from app.pipeline import AGENT_ORDER
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.article_version_repository import ArticleVersionRepository
from app.schemas.article import ArticleInput
from app.schemas.draft import DraftOutput
from app.schemas.outline import OutlineOutput
from app.schemas.persona import PersonaOutput
from app.status import AgentRunStatus, ArticleStatus

logger = logging.getLogger(__name__)


class ArticleWorkflow:
    def __init__(self, session: AsyncSession, agents: list[BaseAgent]) -> None:
        self.session = session
        self.agents = {agent.name: agent for agent in agents}
        self.articles = ArticleRepository(session)
        self.runs = AgentRunRepository(session)
        self.versions = ArticleVersionRepository(session)

    async def run(self, article_id: int, start_from: str | None = None) -> None:
        article = await self.articles.get(article_id)
        if article is None:
            raise NotFoundError(f"article {article_id} not found")
        context = WorkflowContext(article=_article_input(article))
        names = _agents_from(start_from)
        await self._restore_prior(article_id, context, names[0])
        for name in names:
            agent = self.agents[name]
            succeeded = await self._run_agent(article, agent, context)
            if not succeeded:
                return
        article.status = ArticleStatus.COMPLETED
        article.updated_at = utcnow()
        await self.session.commit()
        logger.info(
            "article_id=%s agent_name=%s status=%s execution_time_ms=%s input_tokens=%s output_tokens=%s error=%s",
            article.id,
            "workflow",
            ArticleStatus.COMPLETED,
            "",
            "",
            "",
            "",
        )

    async def _restore_prior(self, article_id: int, context: WorkflowContext, start_name: str) -> None:
        for name in AGENT_ORDER:
            if name == start_name:
                return
            run = await self.runs.latest_success(article_id, name)
            if run is None or run.output_json is None:
                raise InvalidRequestError(f"missing successful output for {name}")
            self._apply(context, name, run.output_json)

    async def _run_agent(self, article: Article, agent: BaseAgent, context: WorkflowContext) -> bool:
        try:
            payload = agent.build_input(context)
            prompt_version = agent.prompt_version
        except Exception as exc:
            await self._record_failure(article, agent.name, None, None, exc, 0)
            return False

        run = await self.runs.start(
            article_id=article.id,
            agent_name=agent.name,
            input_json=payload,
            model=get_settings().openai_model,
            prompt_version=prompt_version,
        )
        await self.session.commit()
        started = time.perf_counter()
        try:
            result = await agent.run(context)
        except Exception as exc:
            elapsed = int((time.perf_counter() - started) * 1000)
            await self._record_failure(article, agent.name, run.id, prompt_version, exc, elapsed)
            return False

        run.status = AgentRunStatus.SUCCESS
        run.output_json = result.output.model_dump(mode="json")
        run.model = result.model
        run.prompt_version = result.prompt_version
        run.input_tokens = result.input_tokens
        run.output_tokens = result.output_tokens
        run.execution_time_ms = result.execution_time_ms
        run.completed_at = utcnow()
        self._apply(context, agent.name, result.output)
        if agent.name == "outline" and context.outline and context.outline.title.strip():
            article.title = context.outline.title[:500]
        if agent.name == "writer" and context.draft:
            article.final_content = context.draft.content_markdown
            await self.versions.add(article.id, context.draft.content_markdown)
        article.updated_at = utcnow()
        await self.session.commit()
        self._log(article.id, agent.name, AgentRunStatus.SUCCESS, result, "")
        return True

    async def _record_failure(
        self,
        article: Article,
        agent_name: str,
        run_id: int | None,
        prompt_version: str | None,
        exc: Exception,
        elapsed: int,
    ) -> None:
        message = public_error_message(exc)
        if run_id is None:
            run = await self.runs.start(
                article_id=article.id,
                agent_name=agent_name,
                input_json={},
                model=get_settings().openai_model,
                prompt_version=prompt_version or "",
            )
        else:
            from app.models.agent_run import AgentRun

            found = await self.session.get(AgentRun, run_id)
            if found is None:
                return
            run = found
        run.status = AgentRunStatus.FAILED
        run.error_message = message
        run.execution_time_ms = elapsed
        run.completed_at = utcnow()
        article.status = ArticleStatus.FAILED
        article.updated_at = utcnow()
        await self.session.commit()
        self._log(article.id, agent_name, AgentRunStatus.FAILED, None, message)
        if not isinstance(exc, Exception) or message == "Agent error":
            logger.info("suppressed sensitive agent error article_id=%s agent_name=%s", article.id, agent_name)

    def _apply(self, context: WorkflowContext, agent_name: str, output: BaseModel | dict) -> None:
        if agent_name == "persona":
            context.persona = PersonaOutput.model_validate(output)
        elif agent_name == "outline":
            context.outline = OutlineOutput.model_validate(output)
        elif agent_name == "writer":
            context.draft = DraftOutput.model_validate(output)

    def _log(
        self,
        article_id: int,
        agent_name: str,
        status: str,
        result: AgentResult | None,
        error: str,
    ) -> None:
        logger.info(
            "article_id=%s agent_name=%s status=%s execution_time_ms=%s input_tokens=%s output_tokens=%s error=%s",
            article_id,
            agent_name,
            status,
            result.execution_time_ms if result else "",
            result.input_tokens if result else "",
            result.output_tokens if result else "",
            error,
        )


def _article_input(article: Article) -> ArticleInput:
    return ArticleInput(
        theme=article.theme,
        keyword=article.keyword,
        media=article.media,
        target_audience=article.target_audience,
        purpose=article.purpose,
        target_length=article.target_length,
        tone=article.tone,
    )


def _agents_from(start_from: str | None) -> list[str]:
    if start_from is None:
        return list(AGENT_ORDER)
    if start_from not in AGENT_ORDER:
        raise InvalidRequestError(f"unknown agent: {start_from}")
    return list(AGENT_ORDER[AGENT_ORDER.index(start_from) :])
