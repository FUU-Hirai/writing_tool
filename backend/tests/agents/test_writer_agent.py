import pytest

from app.agents.context import WorkflowContext
from app.agents.writer import WriterAgent
from app.errors import InvalidRequestError, StructuredOutputError
from app.schemas.article import ArticleInput
from tests.helpers import (
    ARTICLE_PAYLOAD,
    RecordingProvider,
    sample_draft,
    sample_outline,
    sample_persona,
    service_for,
)


def _context() -> WorkflowContext:
    return WorkflowContext(
        article=ArticleInput(**ARTICLE_PAYLOAD),
        persona=sample_persona(),
        outline=sample_outline(),
    )


@pytest.mark.asyncio
async def test_writer_receives_outline_and_does_not_take_review_input() -> None:
    provider = RecordingProvider(sample_draft())
    agent = WriterAgent(service_for(provider))

    result = await agent.run(_context())

    assert "文章を書くことだけ" in provider.system_prompts[0]
    payload = provider.user_contents[0]
    assert "AIツールを選ぶ前にやるべきこと" in payload
    assert "fact_check" not in payload
    assert "seo" not in payload.lower() or "SEO" in provider.system_prompts[0]
    assert result.output.content_markdown.startswith("# AI導入で最初にやるべきこと")
    assert result.output_tokens if False else result.output_tokens == 22


@pytest.mark.asyncio
async def test_writer_requires_outline() -> None:
    agent = WriterAgent(service_for(RecordingProvider(sample_draft())))
    context = WorkflowContext(article=ArticleInput(**ARTICLE_PAYLOAD), persona=sample_persona())
    with pytest.raises(InvalidRequestError):
        await agent.run(context)


@pytest.mark.asyncio
async def test_writer_propagates_parse_error() -> None:
    provider = RecordingProvider(error=StructuredOutputError("Structured output parse error"))
    agent = WriterAgent(service_for(provider))
    with pytest.raises(StructuredOutputError):
        await agent.run(_context())
