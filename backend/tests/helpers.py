from pydantic import BaseModel

from app.schemas.draft import DraftOutput
from app.schemas.outline import OutlineOutput, OutlineSection
from app.schemas.persona import PersonaOutput
from app.schemas.review import ReviewIssue, ReviewOutput
from app.services.llm_service import LLMService, ProviderResult


def sample_persona() -> PersonaOutput:
    return PersonaOutput(
        persona="AI活用を検討している中小企業担当者",
        problems=["何から始めればよいかわからない"],
        needs=["具体的な導入手順を知りたい"],
        knowledge_level="beginner",
        desired_action="AI活用の相談をする",
    )


def sample_outline() -> OutlineOutput:
    return OutlineOutput(
        title="AI導入で最初にやるべきこと",
        sections=[
            OutlineSection(
                heading="AIツールを選ぶ前にやるべきこと",
                purpose="業務整理の重要性を説明する",
                points=["業務を洗い出す", "頻度と負担を確認する"],
            )
        ],
    )


def sample_draft() -> DraftOutput:
    return DraftOutput(
        title="AI導入で最初にやるべきこと",
        content_markdown="# AI導入で最初にやるべきこと\n\nまず業務を洗い出します。",
    )


def sample_review(score: int = 85) -> ReviewOutput:
    return ReviewOutput(
        score=score,
        issues=[
            ReviewIssue(
                type="redundancy",
                target="まず業務を洗い出します。",
                reason="前段と内容が重複している",
                suggestion="削除または統合する",
            )
        ],
        summary="全体として読みやすいが一部重複あり",
    )


class RecordingProvider:
    def __init__(self, output: BaseModel | None = None, error: Exception | None = None) -> None:
        self.output = output
        self.error = error
        self.system_prompts: list[str] = []
        self.user_contents: list[str] = []
        self.response_models: list[type[BaseModel]] = []

    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        response_model: type[BaseModel],
        max_tokens: int,
    ) -> ProviderResult:
        self.system_prompts.append(system_prompt)
        self.user_contents.append(user_content)
        self.response_models.append(response_model)
        if self.error:
            raise self.error
        assert self.output is not None
        return ProviderResult(output=self.output, model="fake-model", input_tokens=11, output_tokens=22)


def service_for(provider: RecordingProvider) -> LLMService:
    return LLMService(provider, model="fake-model", max_tokens=128)


class ScriptedProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.error_for: dict[str, Exception] = {}

    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_content: str,
        response_model: type[BaseModel],
        max_tokens: int,
    ) -> ProviderResult:
        self.calls.append(response_model.__name__)
        error = self.error_for.get(response_model.__name__)
        if error:
            raise error
        output = _output_for(response_model)
        return ProviderResult(output=output, model="test-model", input_tokens=5, output_tokens=7)


def _output_for(response_model: type[BaseModel]) -> BaseModel:
    if response_model.__name__ == "PersonaOutput":
        return sample_persona()
    if response_model.__name__ == "OutlineOutput":
        return sample_outline()
    if response_model.__name__ == "DraftOutput":
        return sample_draft()
    if response_model.__name__ == "ReviewOutput":
        return sample_review(score=10)
    raise AssertionError(response_model.__name__)


ARTICLE_PAYLOAD = {
    "theme": "AI導入で最初にやるべきこと",
    "keyword": "AI 導入",
    "media": "note",
    "target_audience": "AI初心者の企業担当者",
    "purpose": "AIコンサル問い合わせ",
    "target_length": 4000,
    "tone": "実務的で初心者にもわかりやすい",
}
