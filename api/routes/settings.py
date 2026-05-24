"""Settings API routes."""
import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.models import SettingsResponse, SettingsUpdateRequest
from shared.config import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    ENV_PATH,
    MAX_TOKENS,
    OLLAMA_BASE_URL,
    PROJECT_ROOT,
)

router = APIRouter(tags=["settings"])

_JSON_MODE_KEY = "JSON_MODE_DEFAULT"


def _read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            values[k.strip()] = v.strip()
    return values


def _write_env(updates: dict[str, str]) -> None:
    current = _read_env()
    current.update(updates)
    lines = [
        f"OLLAMA_BASE_URL={current.get('OLLAMA_BASE_URL', OLLAMA_BASE_URL)}",
        f"DEFAULT_MODEL={current.get('DEFAULT_MODEL', DEFAULT_MODEL)}",
        f"DEFAULT_TEMPERATURE={current.get('DEFAULT_TEMPERATURE', str(DEFAULT_TEMPERATURE))}",
        f"MAX_TOKENS={current.get('MAX_TOKENS', str(MAX_TOKENS))}",
        f"{_JSON_MODE_KEY}={current.get(_JSON_MODE_KEY, 'false')}",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n")


def _reload_config() -> None:
    import shared.config as cfg

    load_dotenv = __import__("dotenv", fromlist=["load_dotenv"]).load_dotenv
    load_dotenv(ENV_PATH, override=True)
    cfg.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    cfg.DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", DEFAULT_MODEL)
    cfg.DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
    cfg.MAX_TOKENS = int(os.getenv("MAX_TOKENS", str(MAX_TOKENS)))


@router.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    env = _read_env()
    return SettingsResponse(
        ollama_base_url=env.get("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
        default_model=env.get("DEFAULT_MODEL", DEFAULT_MODEL),
        default_temperature=float(env.get("DEFAULT_TEMPERATURE", DEFAULT_TEMPERATURE)),
        max_tokens=int(env.get("MAX_TOKENS", MAX_TOKENS)),
        json_mode_default=env.get(_JSON_MODE_KEY, "false").lower() == "true",
    )


@router.post("/api/settings")
async def save_settings(body: SettingsUpdateRequest):
    updates: dict[str, str] = {}
    if body.ollama_base_url is not None:
        updates["OLLAMA_BASE_URL"] = body.ollama_base_url
    if body.default_model is not None:
        updates["DEFAULT_MODEL"] = body.default_model
    if body.default_temperature is not None:
        updates["DEFAULT_TEMPERATURE"] = str(body.default_temperature)
    if body.max_tokens is not None:
        updates["MAX_TOKENS"] = str(body.max_tokens)
    if body.json_mode_default is not None:
        updates[_JSON_MODE_KEY] = "true" if body.json_mode_default else "false"

    if not ENV_PATH.exists():
        example = PROJECT_ROOT / ".env.example"
        if example.exists():
            ENV_PATH.write_text(example.read_text())

    _write_env(updates)
    _reload_config()
    return await get_settings()
