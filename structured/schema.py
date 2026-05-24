"""Pydantic models for structured JSON outputs."""
from typing import Any

from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    title: str = Field(..., description="Short title for the summary")
    summary: str = Field(..., description="Main summary text")
    key_points: list[str] = Field(default_factory=list, description="Bullet key points")


class QAResponse(BaseModel):
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    sources: list[str] = Field(default_factory=list)


class ListResponse(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "summary": SummaryResponse,
    "qa": QAResponse,
    "list": ListResponse,
}
