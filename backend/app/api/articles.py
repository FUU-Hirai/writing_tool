from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.deps import get_article_service
from app.errors import InvalidRequestError
from app.orchestrators.runner import run_article_workflow
from app.pipeline import AGENT_ORDER
from app.schemas.agent_run import AgentRunRead
from app.schemas.article import ArticleAccepted, ArticleCreate, ArticleDetail, ArticleSummary, ArticleVersionRead
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", response_model=ArticleAccepted, status_code=201)
async def create_article(
    data: ArticleCreate,
    service: ArticleService = Depends(get_article_service),
) -> ArticleAccepted:
    article = await service.create(data)
    return ArticleAccepted(id=article.id, status=article.status)


@router.get("", response_model=list[ArticleSummary])
async def list_articles(service: ArticleService = Depends(get_article_service)) -> list[ArticleSummary]:
    articles = await service.list_articles()
    return [ArticleSummary.model_validate(article) for article in articles]


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: int, service: ArticleService = Depends(get_article_service)) -> ArticleDetail:
    article = await service.get(article_id)
    return ArticleDetail.model_validate(article)


@router.post("/{article_id}/generate", response_model=ArticleAccepted)
async def generate_article(
    article_id: int,
    background: BackgroundTasks,
    service: ArticleService = Depends(get_article_service),
) -> ArticleAccepted:
    article = await service.begin_run(article_id, start_from=None)
    background.add_task(run_article_workflow, article.id, None)
    return ArticleAccepted(id=article.id, status=article.status)


@router.get("/{article_id}/runs", response_model=list[AgentRunRead])
async def list_runs(article_id: int, service: ArticleService = Depends(get_article_service)) -> list[AgentRunRead]:
    runs = await service.list_runs(article_id)
    return [AgentRunRead.model_validate(run) for run in runs]


@router.post("/{article_id}/agents/{agent_name}/retry", response_model=ArticleAccepted)
async def retry_agent(
    article_id: int,
    agent_name: str,
    background: BackgroundTasks,
    service: ArticleService = Depends(get_article_service),
) -> ArticleAccepted:
    if agent_name not in AGENT_ORDER:
        raise InvalidRequestError(f"unknown agent: {agent_name}")
    article = await service.begin_run(article_id, start_from=agent_name)
    background.add_task(run_article_workflow, article.id, agent_name)
    return ArticleAccepted(id=article.id, status=article.status)


@router.get("/{article_id}/versions", response_model=list[ArticleVersionRead])
async def list_versions(
    article_id: int,
    service: ArticleService = Depends(get_article_service),
) -> list[ArticleVersionRead]:
    versions = await service.list_versions(article_id)
    return [ArticleVersionRead.model_validate(version) for version in versions]
