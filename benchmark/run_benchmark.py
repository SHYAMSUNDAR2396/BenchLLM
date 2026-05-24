"""Core benchmark logic — importable as module."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generator

from benchmark.metrics import BenchmarkResult
from shared.config import BENCHMARK_PROMPTS, PROJECT_ROOT
from shared.ollama_client import OllamaClient, OllamaConnectionError
from shared.config import OLLAMA_BASE_URL, DEFAULT_TEMPERATURE
from shared.utils import elapsed_ms, format_metrics, now_ms

RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"

ARCHITECTURE_MAP = {
    "llama3.2": "Llama",
    "llama3": "Llama",
    "mistral": "Mistral",
    "phi3": "Phi",
    "gemma": "Gemma",
}


def _architecture_for(model: str) -> str:
    lower = model.lower()
    for key, arch in ARCHITECTURE_MAP.items():
        if key in lower:
            return arch
    return model.split(":")[0].capitalize() if ":" in model else model.capitalize()


def run_benchmark(
    models: list[str],
    num_prompts: int,
    base_url: str = OLLAMA_BASE_URL,
    temperature: float = DEFAULT_TEMPERATURE,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[list[BenchmarkResult], Path]:
    """
    Run benchmark across models and prompts.
    Calls on_progress with dict events for SSE streaming.
    Returns results and path to saved JSON.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    prompts = BENCHMARK_PROMPTS[: max(1, min(num_prompts, len(BENCHMARK_PROMPTS)))]
    all_results: list[BenchmarkResult] = []

    for model in models:
        client = OllamaClient(base_url, model, temperature)
        per_prompt: list[dict[str, Any]] = []
        tps_values: list[float] = []
        latency_values: list[float] = []

        try:
            if not client.is_available():
                raise OllamaConnectionError("Ollama is not running")
        finally:
            client.close()

        client = OllamaClient(base_url, model, temperature)
        try:
            for idx, prompt in enumerate(prompts, start=1):
                start = now_ms()
                try:
                    result = client.chat(prompt)
                    metrics = format_metrics(
                        result["response"],
                        result["ttft"],
                        result["total_latency"],
                        result.get("token_count"),
                    )
                    metrics["tokens_per_sec"] = result["tokens_per_sec"]
                except OllamaConnectionError:
                    raise
                except Exception as exc:
                    metrics = {
                        "tokens_per_sec": 0.0,
                        "ttft": 0.0,
                        "total_latency": elapsed_ms(start),
                        "token_count": 0,
                        "error": str(exc),
                    }

                tps_values.append(metrics["tokens_per_sec"])
                latency_values.append(metrics["total_latency"])
                per_prompt.append(
                    {
                        "prompt_num": idx,
                        "prompt": prompt[:80],
                        **metrics,
                    }
                )

                if on_progress:
                    on_progress(
                        {
                            "model": model,
                            "prompt_num": idx,
                            "total": len(prompts),
                            "current_tps": metrics["tokens_per_sec"],
                            "status": "running",
                        }
                    )
        finally:
            client.close()

        avg_tps = sum(tps_values) / len(tps_values) if tps_values else 0.0
        avg_lat = sum(latency_values) / len(latency_values) if latency_values else 0.0

        br = BenchmarkResult(
            model=model,
            architecture=_architecture_for(model),
            avg_tokens_per_sec=round(avg_tps, 2),
            avg_latency_ms=round(avg_lat, 2),
            prompts_tested=len(prompts),
            per_prompt=per_prompt,
        )
        all_results.append(br)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    payload = {
        "timestamp": timestamp,
        "models": [r.to_dict() for r in all_results],
    }
    out_path.write_text(json.dumps(payload, indent=2))
    return all_results, out_path


def progress_stream(
    models: list[str], num_prompts: int, **kwargs
) -> Generator[dict[str, Any], None, list[BenchmarkResult]]:
    """Generator that yields progress events then returns results."""
    events: list[dict[str, Any]] = []
    results_holder: list[BenchmarkResult] = []

    def on_progress(event: dict[str, Any]) -> None:
        events.append(event)

    results, _path = run_benchmark(
        models, num_prompts, on_progress=on_progress, **kwargs
    )
    results_holder.extend(results)
    for e in events:
        yield e
    return results_holder
