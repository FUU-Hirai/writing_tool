import pytest

from app.agents.context import WorkflowContext
from app.agents.persona import PersonaAgent
from app.errors import LLMTimeoutError
from app.schemas.article import ArticleInput
from tests.helpers import ARTICLE_PAYLOAD, RecordingProvider, sample_persona, service_for


def _context() -> WorkflowContext:
    return WorkflowContext(article=ArticleInput(**ARTICLE_PAYLOAD))


@pytest.mark.asyncio
async def test_persona_loads_prompt_file_and_returns_structured_output() -> None:
    provider = RecordingProvider(sample_persona())
    agent = PersonaAgent(service_for(provider))

    result = await agent.run(_context())

    assert "読者理解を専門とする編集者" in provider.system_prompts[0]
    assert "AI導入で最初にやるべきこと" in provider.user_contents[0]
    assert provider.response_models == [agent.output_model]
    assert result.prompt_version == "v1"
    assert result.model == "fake-model"
    assert result.input_tokens == 11
    assert result.output.persona == "AI活用を検討している中小企業担当者"
    assert result.output.knowledge_level == "beginner"


@pytest.mark.asyncio
async def test_persona_propagates_timeout() -> None:
    provider = RecordingProvider(error=LLMTimeoutError("OpenAI API timeout"))
    agent = PersonaAgent(service_for(provider))

    with pytest.raises(LLMTimeoutError):
        await agent.run(_context())
