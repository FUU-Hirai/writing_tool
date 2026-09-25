import pytest

from app.agents.context import WorkflowContext
from app.agents.review import ReviewAgent
from app.errors import InvalidRequestError, LLMInvalidResponseError
from app.schemas.article import ArticleInput
from tests.helpers import (
    ARTICLE_PAYLOAD,
    RecordingProvider,
    sample_draft,
    sample_outline,
    sample_persona,
    sample_review,
    service_for,
)


def _context() -> WorkflowContext:
    return WorkflowContext(
        article=ArticleInput(**ARTICLE_PAYLOAD),
        persona=sample_persona(),
        outline=sample_outline(),
        draft=sample_draft(),
    )


@pytest.mark.asyncio
async def test_review_checks_draft_against_persona_and_outline() -> None:
    provider = RecordingProvider(sample_review())
    agent = ReviewAgent(service_for(provider))

    result = await agent.run(_context())

    assert "問題点だけを指摘" in provider.system_prompts[0]
    body = provider.user_contents[0]
    assert "まず業務を洗い出します" in body
    assert "中小企業担当者" in body
    assert "AIツールを選ぶ前にやるべきこと" in body
    assert result.output.score == 85
    assert result.output.issues[0].type == "redundancy"
    assert result.prompt_version == "v1"


@pytest.mark.asyncio
async def test_review_requires_draft() -> None:
    agent = ReviewAgent(service_for(RecordingProvider(sample_review())))
    with pytest.raises(InvalidRequestError):
        await agent.run(WorkflowContext(article=ArticleInput(**ARTICLE_PAYLOAD)))


@pytest.mark.asyncio
async def test_review_propagates_invalid_response() -> None:
    provider = RecordingProvider(error=LLMInvalidResponseError("OpenAI API error"))
    agent = ReviewAgent(service_for(provider))
    with pytest.raises(LLMInvalidResponseError):
        await agent.run(_context())
