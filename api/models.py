"""Pydantic request/response models for API layer."""
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str
    model: str | None = None
    temperature: float | None = None
    json_mode: bool = False
    schema_name: str = "summary"


class ChatMetrics(BaseModel):
    tokens_per_sec: float
    ttft: float
    total_latency: float
    token_count: int


class ChatJsonResponse(BaseModel):
    data: dict[str, Any]
    metrics: ChatMetrics


class StatusResponse(BaseModel):
    ollama_running: bool
    models: list[str]
    active_model: str


class BenchmarkRunRequest(BaseModel):
    models: list[str]
    num_prompts: int = 10


class ComparisonRunRequest(BaseModel):
    models: list[str] | None = None


class SettingsResponse(BaseModel):
    ollama_base_url: str
    default_model: str
    default_temperature: float
    max_tokens: int
    json_mode_default: bool = False


class SettingsUpdateRequest(BaseModel):
    ollama_base_url: str | None = None
    default_model: str | None = None
    default_temperature: float | None = None
    max_tokens: int | None = None
    json_mode_default: bool | None = None


class ErrorResponse(BaseModel):
    detail: str
    error_type: str = "OllamaConnectionError"
