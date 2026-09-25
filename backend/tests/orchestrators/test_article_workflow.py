import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import WorkflowContext
from app.clock import utcnow
from app.errors import LLMTimeoutError
from app.models import Base
from app.models.agent_run import AgentRun
from app.models.article import Article
from app.orchestrators.article_workflow import ArticleWorkflow
from app.schemas.article import ArticleCreate
from app.services.article_service import ArticleService
from app.status import AgentRunStatus, ArticleStatus
from tests.helpers import ARTICLE_PAYLOAD, sample_draft, sample_outline, sample_persona, sample_review


class FakeAgent(BaseAgent):
    output_model = sample_persona().__class__

    def __init__(self, name: str, output=None, error: Exception | None = None) -> None:
        self.name = name
        self.output = output
        self.error = error
        self.calls = 0

    @property
    def prompt_version(self) -> str:
        return "v1"

    def build_input(self, context: WorkflowContext) -> dict:
        return {"agent": self.name, "theme": context.article.theme}

    async def run(self, context: WorkflowContext) -> AgentResult:
        self.calls += 1
        if self.error:
            raise self.error
        return AgentResult(
            output=self.output,
            model="fake-model",
            prompt_version="v1",
            input_tokens=3,
            output_tokens=4,
            execution_time_ms=15,
        )


@pytest.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


def _agents(writer_error: Exception | None = None) -> list[FakeAgent]:
    return [
        FakeAgent("persona", sample_persona()),
        FakeAgent("outline", sample_outline()),
        FakeAgent("writer", sample_draft(), error=writer_error),
        FakeAgent("review", sample_review(score=10)),
    ]


async def _create(session) -> Article:
    article = await ArticleService(session).create(ArticleCreate(**ARTICLE_PAYLOAD))
    await session.commit()
    return article


@pytest.mark.asyncio
async def test_low_review_score_still_completes_and_stores_version(session) -> None:
    article = await _create(session)
    agents = _agents()
    await ArticleWorkflow(session, agents).run(article.id)

    stored = await session.get(Article, article.id)
    assert stored.status == ArticleStatus.COMPLETED
    assert stored.title == "AI導入で最初にやるべきこと"
    assert stored.final_content.startswith("# AI導入")
    runs = (await session.execute(AgentRun.__table__.select())).scalars().all() if False else None
    from sqlalchemy import select

    runs = list((await session.execute(select(AgentRun).order_by(AgentRun.id))).scalars().all())
    assert [run.agent_name for run in runs] == ["persona", "outline", "writer", "review"]
    assert all(run.status == AgentRunStatus.SUCCESS for run in runs)
    assert runs[0].prompt_version == "v1"
    assert runs[0].input_tokens == 3
    assert runs[3].output_json["score"] == 10
    versions = await ArticleService(session).list_versions(article.id)
    assert len(versions) == 1
    assert [agent.calls for agent in agents] == [1, 1, 1, 1]


@pytest.mark.asyncio
async def test_writer_failure_is_saved_and_review_is_not_called(session) -> None:
    article = await _create(session)
    agents = _agents(writer_error=LLMTimeoutError("OpenAI API timeout"))
    await ArticleWorkflow(session, agents).run(article.id)

    stored = await session.get(Article, article.id)
    assert stored.status == ArticleStatus.FAILED
    assert stored.final_content is None
    from sqlalchemy import select

    runs = list((await session.execute(select(AgentRun).order_by(AgentRun.id))).scalars().all())
    assert [run.agent_name for run in runs] == ["persona", "outline", "writer"]
    assert runs[-1].status == AgentRunStatus.FAILED
    assert runs[-1].error_message == "OpenAI API timeout"
    assert agents[3].calls == 0


@pytest.mark.asyncio
async def test_retry_from_writer_reuses_previous_outputs(session) -> None:
    article = await _create(session)
    now = utcnow()
    session.add_all(
        [
            AgentRun(
                article_id=article.id,
                agent_name="persona",
                status=AgentRunStatus.SUCCESS,
                input_json={"article": ARTICLE_PAYLOAD},
                output_json=sample_persona().model_dump(),
                model="fake-model",
                prompt_version="v1",
                input_tokens=1,
                output_tokens=1,
                execution_time_ms=1,
                started_at=now,
                completed_at=now,
                created_at=now,
            ),
            AgentRun(
                article_id=article.id,
                agent_name="outline",
                status=AgentRunStatus.SUCCESS,
                input_json={},
                output_json=sample_outline().model_dump(),
                model="fake-model",
                prompt_version="v1",
                input_tokens=1,
                output_tokens=1,
                execution_time_ms=1,
                started_at=now,
                completed_at=now,
                created_at=now,
            ),
        ]
    )
    article.status = ArticleStatus.FAILED
    await session.commit()

    agents = _agents()
    await ArticleWorkflow(session, agents).run(article.id, start_from="writer")

    assert agents[0].calls == 0
    assert agents[1].calls == 0
    assert agents[2].calls == 1
    assert agents[3].calls == 1
    stored = await session.get(Article, article.id)
    assert stored.status == ArticleStatus.COMPLETED
    versions = await ArticleService(session).list_versions(article.id)
    assert [version.version for version in versions] == [1]


@pytest.mark.asyncio
async def test_secret_like_error_is_not_stored(session, caplog) -> None:
    article = await _create(session)
    agents = _agents(writer_error=RuntimeError("failed with sk-secretvalue"))
    await ArticleWorkflow(session, agents).run(article.id)

    from sqlalchemy import select

    runs = list((await session.execute(select(AgentRun))).scalars().all())
    writer = [run for run in runs if run.agent_name == "writer"][0]
    assert writer.error_message == "Agent error"
    assert "sk-" not in caplog.text
