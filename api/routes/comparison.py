"""Comparison API routes."""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from api.models import ComparisonRunRequest, ErrorResponse
from comparison.report import generate_report
from comparison.run_comparison import load_comparison_results, run_comparison
from shared.ollama_client import OllamaConnectionError

router = APIRouter(tags=["comparison"])


@router.post("/api/comparison/run")
async def comparison_run(request: Request, body: ComparisonRunRequest | None = None):
    models = body.models if body and body.models else None

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        events_acc: list[dict] = []

        def on_progress(e: dict) -> None:
            events_acc.append(e)

        def _run():
            try:
                run_comparison(models=models, on_progress=on_progress)
                return None
            except OllamaConnectionError as exc:
                return exc

        err = await loop.run_in_executor(None, _run)

        for event in events_acc:
            if await request.is_disconnected():
                return
            yield f"data: {json.dumps(event)}\n\n"

        if err:
            yield f"data: {json.dumps({'status': 'error', 'detail': str(err)})}\n\n"
        elif not await request.is_disconnected():
            yield f"data: {json.dumps({'status': 'complete'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/api/comparison/report")
async def comparison_report():
    md = generate_report()
    return PlainTextResponse(content=md, media_type="text/markdown")


@router.get("/api/comparison/results")
async def comparison_results():
    return load_comparison_results()
