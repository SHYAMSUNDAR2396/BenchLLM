"""Benchmark API routes."""
import json
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from api.models import BenchmarkRunRequest, ErrorResponse
from benchmark.run_benchmark import run_benchmark
from shared.config import PROJECT_ROOT
from shared.ollama_client import OllamaConnectionError

router = APIRouter(tags=["benchmark"])
RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"


@router.post("/api/benchmark/run")
async def run_benchmark_endpoint(request: Request, body: BenchmarkRunRequest):
    async def event_generator() -> AsyncGenerator[str, None]:
        results_holder: list = []

        import asyncio

        loop = asyncio.get_event_loop()

        def _run_sync():
            nonlocal results_holder
            events_acc: list[dict] = []

            def progress(e: dict) -> None:
                events_acc.append(e)

            try:
                results, _path = run_benchmark(
                    body.models,
                    body.num_prompts,
                    on_progress=progress,
                )
                results_holder = results
                return events_acc, None
            except OllamaConnectionError as exc:
                return events_acc, exc

        events_acc, err = await loop.run_in_executor(None, _run_sync)

        for event in events_acc:
            if await request.is_disconnected():
                return
            yield f"data: {json.dumps(event)}\n\n"

        if err:
            yield f"data: {json.dumps({'status': 'error', 'detail': str(err)})}\n\n"
            return

        if not await request.is_disconnected():
            yield f"data: {json.dumps({'status': 'complete', 'results': [r.to_dict() for r in results_holder]})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/api/benchmark/latest")
async def get_latest_benchmark():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(RESULTS_DIR.glob("benchmark_*.json"), reverse=True)
    if not files:
        return JSONResponse(status_code=404, content={"detail": "No benchmark results yet"})
    return json.loads(files[0].read_text())
