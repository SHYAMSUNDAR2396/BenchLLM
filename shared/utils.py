"""Timing helpers, token counter, and diff utilities."""
import difflib
import time
from typing import Any


def now_ms() -> float:
    return time.perf_counter() * 1000


def elapsed_ms(start: float) -> float:
    return time.perf_counter() * 1000 - start


def count_tokens_approx(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def compute_tokens_per_sec(token_count: int, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return round(token_count / duration_sec, 2)


def text_diff(a: str, b: str) -> str:
    """Unified diff between two strings."""
    lines_a = a.splitlines(keepends=True)
    lines_b = b.splitlines(keepends=True)
    diff = difflib.unified_diff(lines_a, lines_b, fromfile="temp_0.0", tofile="temp_0.7")
    return "".join(diff)


def format_metrics(
    response: str,
    ttft_ms: float,
    total_latency_ms: float,
    token_count: int | None = None,
) -> dict[str, Any]:
    tokens = token_count if token_count is not None else count_tokens_approx(response)
    duration_sec = max(total_latency_ms / 1000, 0.001)
    return {
        "tokens_per_sec": compute_tokens_per_sec(tokens, duration_sec),
        "ttft": round(ttft_ms, 2),
        "total_latency": round(total_latency_ms, 2),
        "token_count": tokens,
    }
