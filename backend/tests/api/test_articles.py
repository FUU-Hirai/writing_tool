import pytest
from fastapi.testclient import TestClient

from app.container import container
from app.main import create_app
from app.services.llm_service import LLMService
from tests.helpers import ARTICLE_PAYLOAD, ScriptedProvider


@pytest.fixture
def provider() -> ScriptedProvider:
    scripted = ScriptedProvider()
    container.llm_service_factory = lambda: LLMService(scripted, model="test-model", max_tokens=128)
    yield scripted
    from app.container import default_llm_service

    container.llm_service_factory = default_llm_service


@pytest.fixture
def client(provider: ScriptedProvider) -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_list_and_get_article(client: TestClient) -> None:
    created = client.post("/api/articles", json=ARTICLE_PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "draft"
    article_id = body["id"]

    listing = client.get("/api/articles")
    assert listing.status_code == 200
    assert listing.json()[0]["theme"] == ARTICLE_PAYLOAD["theme"]
    assert "final_content" not in listing.json()[0]

    detail = client.get(f"/api/articles/{article_id}")
    assert detail.status_code == 200
    assert detail.json()["keyword"] == "AI 導入"
    assert detail.json()["final_content"] is None


def test_generate_persists_runs_tokens_and_version(client: TestClient, provider: ScriptedProvider) -> None:
    article_id = client.post("/api/articles", json=ARTICLE_PAYLOAD).json()["id"]
    generated = client.post(f"/api/articles/{article_id}/generate")
    assert generated.status_code == 200
    assert generated.json()["status"] == "processing"

    detail = client.get(f"/api/articles/{article_id}").json()
    assert detail["status"] == "completed"
    assert detail["final_content"].startswith("# AI導入")
    assert detail["title"] == "AI導入で最初にやるべきこと"

    runs = client.get(f"/api/articles/{article_id}/runs").json()
    assert [run["agent_name"] for run in runs] == ["persona", "outline", "writer", "review"]
    assert runs[0]["input_tokens"] == 5
    assert runs[0]["output_tokens"] == 7
    assert runs[0]["prompt_version"] == "v1"
    assert runs[0]["input_json"]["article"]["theme"] == ARTICLE_PAYLOAD["theme"]
    assert runs[2]["output_json"]["content_markdown"].startswith("# AI導入")

    versions = client.get(f"/api/articles/{article_id}/versions").json()
    assert len(versions) == 1
    assert versions[0]["version"] == 1
    assert provider.calls == ["PersonaOutput", "OutlineOutput", "DraftOutput", "ReviewOutput"]


def test_writer_failure_is_visible_on_runs(client: TestClient, provider: ScriptedProvider) -> None:
    from app.errors import LLMTimeoutError

    provider.error_for["DraftOutput"] = LLMTimeoutError("OpenAI API timeout")
    article_id = client.post("/api/articles", json=ARTICLE_PAYLOAD).json()["id"]
    client.post(f"/api/articles/{article_id}/generate")

    detail = client.get(f"/api/articles/{article_id}").json()
    assert detail["status"] == "failed"
    runs = client.get(f"/api/articles/{article_id}/runs").json()
    writer = runs[-1]
    assert writer["agent_name"] == "writer"
    assert writer["status"] == "failed"
    assert writer["error_message"] == "OpenAI API timeout"


def test_retry_writer_after_failure(client: TestClient, provider: ScriptedProvider) -> None:
    from app.errors import LLMTimeoutError

    provider.error_for["DraftOutput"] = LLMTimeoutError("OpenAI API timeout")
    article_id = client.post("/api/articles", json=ARTICLE_PAYLOAD).json()["id"]
    client.post(f"/api/articles/{article_id}/generate")
    provider.error_for.pop("DraftOutput")

    retried = client.post(f"/api/articles/{article_id}/agents/writer/retry")
    assert retried.status_code == 200
    assert client.get(f"/api/articles/{article_id}").json()["status"] == "completed"
    assert provider.calls.count("PersonaOutput") == 1
    assert provider.calls.count("DraftOutput") == 2


def test_unknown_agent_and_missing_article(client: TestClient) -> None:
    article_id = client.post("/api/articles", json=ARTICLE_PAYLOAD).json()["id"]
    unknown = client.post(f"/api/articles/{article_id}/agents/seo/retry")
    assert unknown.status_code == 400
    missing = client.get("/api/articles/9999")
    assert missing.status_code == 404


def test_retry_without_prior_success_is_rejected(client: TestClient) -> None:
    article_id = client.post("/api/articles", json=ARTICLE_PAYLOAD).json()["id"]
    response = client.post(f"/api/articles/{article_id}/agents/writer/retry")
    assert response.status_code == 400


def test_validation_error(client: TestClient) -> None:
    payload = dict(ARTICLE_PAYLOAD)
    payload["target_length"] = 10
    response = client.post("/api/articles", json=payload)
    assert response.status_code == 422
