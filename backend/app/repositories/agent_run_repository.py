from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.models.agent_run import AgentRun
from app.status import AgentRunStatus


class AgentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start(
        self,
        *,
        article_id: int,
        agent_name: str,
        input_json: dict,
        model: str,
        prompt_version: str,
    ) -> AgentRun:
        now = utcnow()
        run = AgentRun(
            article_id=article_id,
            agent_name=agent_name,
            status=AgentRunStatus.RUNNING,
            input_json=input_json,
            output_json=None,
            model=model,
            prompt_version=prompt_version,
            input_tokens=None,
            output_tokens=None,
            execution_time_ms=None,
            error_message=None,
            started_at=now,
            completed_at=None,
            created_at=now,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def list_for_article(self, article_id: int) -> list[AgentRun]:
        result = await self.session.execute(
            select(AgentRun).where(AgentRun.article_id == article_id).order_by(AgentRun.id.asc())
        )
        return list(result.scalars().all())

    async def latest_success(self, article_id: int, agent_name: str) -> AgentRun | None:
        result = await self.session.execute(
            select(AgentRun)
            .where(
                AgentRun.article_id == article_id,
                AgentRun.agent_name == agent_name,
                AgentRun.status == AgentRunStatus.SUCCESS,
            )
            .order_by(AgentRun.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
