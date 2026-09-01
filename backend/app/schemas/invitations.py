from __future__ import annotations

from pydantic import BaseModel, Field


class InvitationIssueRequest(BaseModel):
    count: int = Field(gt=0, le=1000)


class InvitationBatchRead(BaseModel):
    tokens: list[str]


class InvitationSummaryRead(BaseModel):
    total: int
    pending: int
    consumed: int
    expired: int
