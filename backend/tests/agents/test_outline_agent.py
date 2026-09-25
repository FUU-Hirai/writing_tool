import pytest

from app.agents.context import WorkflowContext
from app.agents.outline import OutlineAgent
from app.errors import InvalidRequestError, LLMRateLimitError
from app.schemas.article import ArticleInput
from tests.helpers import ARTICLE_PAYLOAD, RecordingProvider, sample_outline, sample_persona, service_for


def _context() -> WorkflowContext:
    return WorkflowContext(article=ArticleInput(**ARTICLE_PAYLOAD), persona=sample_persona())


@pytest.mark.asyncio
async def test_outline_uses_persona_and_prompt_file() -> None:
    provider = RecordingProvider(sample_outline())
    agent = OutlineAgent(service_for(provider))

    result = await agent.run(_context())

    assert "記事構成を専門とする編集者" in provider.system_prompts[0]
    assert "中小企業担当者" in provider.user_contents[0]
    assert result.output.title == "AI導入で最初にやるべきこと"
    assert result.output.sections[0].heading == "AIツールを選ぶ前にやるべきこと"
    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_outline_requires_persona() -> None:
    agent = OutlineAgent(service_for(RecordingProvider(sample_outline())))
    with pytest.raises(InvalidRequestError):
        await agent.run(WorkflowContext(article=ArticleInput(**ARTICLE_PAYLOAD)))


@pytest.mark.asyncio
async def test_outline_propagates_rate_limit() -> None:
    provider = RecordingProvider(error=LLMRateLimitError("OpenAI API rate limit"))
    agent = OutlineAgent(service_for(provider))
    with pytest.raises(LLMRateLimitError):
        await agent.run(_context())
