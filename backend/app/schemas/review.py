from pydantic import BaseModel, Field, field_validator


class ReviewIssue(BaseModel):
    type: str
    target: str
    reason: str
    suggestion: str


class ReviewOutput(BaseModel):
    score: int = Field(description="0から100の参考スコア。合格判定には使わない")
    issues: list[ReviewIssue]
    summary: str

    @field_validator("score")
    @classmethod
    def clamp_score(cls, value: int) -> int:
        return max(0, min(100, value))
