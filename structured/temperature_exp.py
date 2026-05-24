"""Run prompts at temperature 0.0 vs 0.7 and save diff."""
import json
from datetime import datetime
from pathlib import Path

from shared.config import DEFAULT_MODEL, OLLAMA_BASE_URL, PROJECT_ROOT
from shared.ollama_client import OllamaClient
from shared.utils import text_diff

OUTPUT_DIR = PROJECT_ROOT / "structured" / "outputs"


def run_temperature_experiment(
    prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = OLLAMA_BASE_URL,
) -> Path:
    """Compare responses at temp 0.0 and 0.7; save JSON + diff."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results: dict[str, str] = {}
    for temp in (0.0, 0.7):
        client = OllamaClient(base_url, model, temp)
        try:
            out = client.chat(prompt)
            results[f"temp_{temp}"] = out["response"]
        finally:
            client.close()

    diff = text_diff(results["temp_0.0"], results["temp_0.7"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "prompt": prompt,
        "model": model,
        "temp_0.0": results["temp_0.0"],
        "temp_0.7": results["temp_0.7"],
        "diff": diff,
    }
    path = OUTPUT_DIR / f"temp_exp_{timestamp}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path
