import logging

from app.agents.outline import OutlineAgent
from app.agents.persona import PersonaAgent
from app.agents.review import ReviewAgent
from app.agents.writer import WriterAgent
from app.container import container
from app.database import session_factory
from app.errors import public_error_message
from app.orchestrators.article_workflow import ArticleWorkflow
from app.status import ArticleStatus

logger = logging.getLogger(__name__)


def build_workflow(session) -> ArticleWorkflow:
    llm = container.llm_service_factory()
    agents = [
        PersonaAgent(llm),
        OutlineAgent(llm),
        WriterAgent(llm),
        ReviewAgent(llm),
    ]
    return ArticleWorkflow(session, agents)


async def run_article_workflow(article_id: int, start_from: str | None = None) -> None:
    try:
        async with session_factory() as session:
            workflow = build_workflow(session)
            await workflow.run(article_id, start_from=start_from)
    except Exception as exc:
        logger.info(
            "article_id=%s agent_name=%s status=%s execution_time_ms=%s input_tokens=%s output_tokens=%s error=%s",
            article_id,
            "workflow",
            "failed",
            "",
            "",
            "",
            public_error_message(exc),
        )
        await _mark_failed(article_id)


async def _mark_failed(article_id: int) -> None:
    try:
        async with session_factory() as session:
            from app.repositories.article_repository import ArticleRepository

            article = await ArticleRepository(session).get(article_id)
            if article is None:
                return
            article.status = ArticleStatus.FAILED
            from app.clock import utcnow

            article.updated_at = utcnow()
            await session.commit()
    except Exception:
        logger.info("article_id=%s agent_name=workflow status=failed error=DB error", article_id)
