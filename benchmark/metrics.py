"""Benchmark result dataclass."""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BenchmarkResult:
    model: str
    architecture: str
    avg_tokens_per_sec: float
    avg_latency_ms: float
    prompts_tested: int
    per_prompt: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
