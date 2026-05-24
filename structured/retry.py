"""Retry helper for structured output validation."""
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def with_retry(fn: Callable[[], T], max_attempts: int = 2, delay_sec: float = 0.5) -> T:
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(delay_sec)
    raise last_exc  # type: ignore[misc]
