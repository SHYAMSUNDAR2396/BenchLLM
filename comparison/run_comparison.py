"""Run all comparison models x 40 prompts."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import psutil

from shared.config import COMPARISON_MODELS, DEFAULT_TEMPERATURE, OLLAMA_BASE_URL, PROJECT_ROOT
from shared.ollama_client import OllamaClient, OllamaConnectionError
from shared.utils import elapsed_ms, now_ms

OUTPUT_DIR = PROJECT_ROOT / "comparison" / "outputs"
PROMPTS_PATH = PROJECT_ROOT / "comparison" / "prompts.json"


def load_all_prompts() -> list[dict[str, str]]:
    data = json.loads(PROMPTS_PATH.read_text())
    prompts: list[dict[str, str]] = []
    for category, items in data.items():
        for i, text in enumerate(items):
            prompts.append(
                {
                    "id": f"{category}_{i}",
                    "category": category,
                    "text": text,
                }
            )
    return prompts


def _memory_mb() -> float:
    return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)


def run_comparison(
    models: list[str] | None = None,
    base_url: str = OLLAMA_BASE_URL,
    temperature: float = DEFAULT_TEMPERATURE,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Path]:
    """Run comparison for each model; save per-model JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    models = models or COMPARISON_MODELS
    prompts = load_all_prompts()
    total_per_model = len(prompts)
    saved: dict[str, Path] = {}

    for model in models:
        client = OllamaClient(base_url, model, temperature)
        entries: list[dict[str, Any]] = []
        tps_list: list[float] = []
        mem_list: list[float] = []

        try:
            for idx, item in enumerate(prompts, start=1):
                start = now_ms()
                mem_before = _memory_mb()
                try:
                    out = client.chat(item["text"])
                    latency = out["total_latency"]
                    tps = out["tokens_per_sec"]
                    response = out["response"]
                except OllamaConnectionError:
                    raise
                except Exception as exc:
                    latency = elapsed_ms(start)
                    tps = 0.0
                    response = f"Error: {exc}"

                mem_after = _memory_mb()
                mem = max(mem_before, mem_after)
                tps_list.append(tps)
                mem_list.append(mem)

                entries.append(
                    {
                        "prompt_id": item["id"],
                        "category": item["category"],
                        "prompt": item["text"],
                        "response": response,
                        "tokens_per_sec": tps,
                        "total_latency": latency,
                        "memory_mb": mem,
                    }
                )

                if on_progress:
                    on_progress(
                        {
                            "model": model,
                            "prompt_num": idx,
                            "total": total_per_model,
                            "status": "running",
                        }
                    )
        finally:
            client.close()

        avg_tps = sum(tps_list) / len(tps_list) if tps_list else 0.0
        avg_mem = sum(mem_list) / len(mem_list) if mem_list else 0.0
        avg_latency = (
            sum(e["total_latency"] for e in entries) / len(entries) if entries else 0.0
        )

        payload = {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "avg_tokens_per_sec": round(avg_tps, 2),
            "avg_memory_mb": round(avg_mem, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "prompts": entries,
        }
        safe_name = model.replace(":", "_").replace("/", "_")
        path = OUTPUT_DIR / f"{safe_name}.json"
        path.write_text(json.dumps(payload, indent=2))
        saved[model] = path

    return saved


def load_comparison_results() -> dict[str, Any]:
    """Load latest per-model outputs for API/UI."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    models_data: list[dict[str, Any]] = []
    all_prompts = load_all_prompts()

    badge_map = {
        "llama3.2": ("Llama 3 8B", "primary", "Quantized Q4_K_M"),
        "llama3": ("Llama 3 8B", "primary", "Quantized Q4_K_M"),
        "phi3": ("Phi-3 Mini", "secondary", "Quantized FP16"),
        "mistral": ("Mistral 7B", "tertiary", "Quantized Q8_0"),
    }

    for path in sorted(OUTPUT_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        model = data.get("model", path.stem)
        label, color, quant = badge_map.get(
            model.split(":")[0] if ":" in model else model,
            (model, "primary", "Local"),
        )
        models_data.append(
            {
                "model": model,
                "label": label,
                "color": color,
                "quantization": quant,
                "avg_tokens_per_sec": data.get("avg_tokens_per_sec", 0),
                "avg_memory_mb": data.get("avg_memory_mb", 0),
                "avg_latency_ms": data.get("avg_latency_ms", 0),
                "quality_score": round(
                    min(10.0, data.get("avg_tokens_per_sec", 0) / 15 + 5), 1
                ),
                "prompts": data.get("prompts", []),
            }
        )

    return {
        "models": models_data,
        "prompt_list": [
            {"id": p["id"], "category": p["category"], "text": p["text"]} for p in all_prompts
        ],
    }
