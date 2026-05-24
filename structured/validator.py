"""Inject JSON schema into prompts and validate responses."""
import json
import re
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from structured.schema import SCHEMA_REGISTRY, ListResponse, QAResponse, SummaryResponse


def _schema_json(model: Type[BaseModel]) -> str:
    return json.dumps(model.model_json_schema(), indent=2)


def enforce_json_output(
    prompt: str,
    schema_name: str = "summary",
) -> tuple[str, Type[BaseModel]]:
    """
    Augment prompt with schema instructions.
    Returns (augmented_prompt, model_class).
    """
    model_cls = SCHEMA_REGISTRY.get(schema_name, SummaryResponse)
    schema_str = _schema_json(model_cls)
    augmented = (
        f"{prompt}\n\n"
        "Respond with ONLY valid JSON matching this schema (no markdown, no prose):\n"
        f"{schema_str}"
    )
    return augmented, model_cls


def extract_json(text: str) -> dict[str, Any]:
    """Extract JSON object from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def validate_response(text: str, model_cls: Type[BaseModel]) -> BaseModel:
    data = extract_json(text)
    return model_cls.model_validate(data)
