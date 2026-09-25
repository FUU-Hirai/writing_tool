from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    agent_name: str
    status: str
    input_json: dict | None
    output_json: dict | None
    model: str | None
    prompt_version: str | None
    input_tokens: int | None
    output_tokens: int | None
    execution_time_ms: int | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
