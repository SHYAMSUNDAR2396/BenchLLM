"""Chat and status routes."""
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from api.models import ChatJsonResponse, ChatMetrics, ChatRequest, ErrorResponse, StatusResponse
from shared.config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, OLLAMA_BASE_URL
from shared.ollama_client import OllamaClient, OllamaConnectionError, resolve_model
from shared.utils import count_tokens_approx, elapsed_ms, format_metrics, now_ms
from structured.retry import with_retry
from structured.validator import enforce_json_output, validate_response

router = APIRouter(tags=["chat"])


def _error_response(exc: OllamaConnectionError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


@router.get("/api/status", response_model=StatusResponse)
async def get_status():
    client = OllamaClient(OLLAMA_BASE_URL, DEFAULT_MODEL, DEFAULT_TEMPERATURE)
    try:
        running = client.is_available()
        models = client.list_models() if running else []
    except OllamaConnectionError:
        running = False
        models = []
    finally:
        client.close()
    active = DEFAULT_MODEL
    if running and models:
        try:
            active = resolve_model(DEFAULT_MODEL, OLLAMA_BASE_URL)
        except OllamaConnectionError:
            active = models[0]

    return StatusResponse(
        ollama_running=running,
        models=models,
        active_model=active,
    )


@router.post("/api/chat")
async def chat(request: Request, body: ChatRequest):
    model = body.model or DEFAULT_MODEL
    temperature = body.temperature if body.temperature is not None else DEFAULT_TEMPERATURE

    if body.json_mode:
        return await _chat_json(body, model, temperature)

    return await _chat_stream(request, body.prompt, model, temperature)


async def _chat_json(body: ChatRequest, model: str, temperature: float):
    augmented, model_cls = enforce_json_output(body.prompt, body.schema_name)

    def _run():
        client = OllamaClient(OLLAMA_BASE_URL, model, temperature)
        try:
            out = client.chat(augmented)
            validated = validate_response(out["response"], model_cls)
            return out, validated
        finally:
            client.close()

    try:
        out, validated = with_retry(_run, max_attempts=2)
    except OllamaConnectionError as exc:
        return _error_response(exc)
    except Exception as exc:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "error_type": "ValidationError"},
        )

    metrics = ChatMetrics(
        tokens_per_sec=out["tokens_per_sec"],
        ttft=out["ttft"],
        total_latency=out["total_latency"],
        token_count=out["token_count"],
    )
    return ChatJsonResponse(data=validated.model_dump(), metrics=metrics)


async def _chat_stream(
    request: Request, prompt: str, model: str, temperature: float
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        client = OllamaClient(OLLAMA_BASE_URL, model, temperature)
        start = now_ms()
        full_text = ""

        try:
            if not client.is_available():
                yield f"data: {json.dumps({'error': 'Ollama is not running. Start with: ollama serve', 'done': True})}\n\n"
                return

            for token in client.stream_chat(prompt):
                if await request.is_disconnected():
                    break
                full_text += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            if not await request.is_disconnected():
                metrics = format_metrics(
                    full_text,
                    client.last_ttft_ms,
                    client.last_total_ms or elapsed_ms(start),
                    count_tokens_approx(full_text),
                )
                yield f"data: {json.dumps({'token': '', 'done': True, 'metrics': metrics})}\n\n"
        except OllamaConnectionError as exc:
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
        finally:
            client.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
