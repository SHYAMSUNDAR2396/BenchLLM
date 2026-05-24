"""Ollama HTTP client — all Ollama calls go through this module."""
import json
from collections.abc import Generator
from typing import Any

import httpx

from shared.config import MAX_TOKENS
from shared.utils import count_tokens_approx, elapsed_ms, now_ms


def _read_error_body(response: httpx.Response) -> str:
    """Read error body from streaming or non-streaming responses."""
    try:
        if response.is_closed:
            return getattr(response, "_content", b"").decode(errors="replace")
        raw = response.read()
        return raw.decode(errors="replace") if isinstance(raw, bytes) else str(raw)
    except Exception:
        return "(unable to read response body)"


def resolve_model(requested: str, base_url: str) -> str:
    """Map requested model name to an installed Ollama model."""
    client = httpx.Client(timeout=httpx.Timeout(10.0, connect=5.0))
    try:
        resp = client.get(f"{base_url.rstrip('/')}/api/tags")
        resp.raise_for_status()
        available = [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
    except httpx.HTTPError as exc:
        raise OllamaConnectionError(f"Cannot list models: {exc}") from exc
    finally:
        client.close()

    if requested in available:
        return requested

    req_stem = requested.split(":")[0].lower()
    # llama3.2 -> llama3 family for matching llama3:latest
    family = req_stem.rsplit(".", 1)[0] if "." in req_stem and ":" not in requested else req_stem

    for name in available:
        name_base = name.split(":")[0].lower()
        if name_base == req_stem or name.lower().startswith(f"{req_stem}:"):
            return name
        if name_base == family or name.lower().startswith(f"{family}:"):
            return name

    raise OllamaConnectionError(
        f"Model '{requested}' not found. Available: {', '.join(available) or 'none'}. "
        f"Run: ollama pull {requested}"
    )


class OllamaConnectionError(Exception):
    """Raised when Ollama is unreachable or returns an error."""

    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float, resolve: bool = True):
        self.base_url = base_url.rstrip("/")
        self.model = resolve_model(model, self.base_url) if resolve else model
        self.temperature = temperature
        self._client = httpx.Client(timeout=httpx.Timeout(300.0, connect=5.0))
        self.last_ttft_ms: float = 0.0
        self.last_total_ms: float = 0.0

    def _chat_payload(self, prompt: str, stream: bool) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": MAX_TOKENS,
            },
        }

    def is_available(self) -> bool:
        try:
            resp = self._client.get(f"{self.base_url}/api/tags")
            return resp.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    def list_models(self) -> list[str]:
        try:
            resp = self._client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise OllamaConnectionError(f"Cannot list models: {exc}") from exc

    def stream_chat(self, prompt: str) -> Generator[str, None, None]:
        """Stream tokens; stores ttft on the generator object as `.ttft_ms`."""
        start = now_ms()
        first_token_at: float | None = None
        url = f"{self.base_url}/api/chat"

        try:
            with self._client.stream(
                "POST", url, json=self._chat_payload(prompt, stream=True)
            ) as response:
                if response.status_code >= 400:
                    body = _read_error_body(response)
                    raise OllamaConnectionError(
                        f"Ollama returned {response.status_code}: {body}"
                    )
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    message = chunk.get("message", {})
                    token = message.get("content", "")
                    if token:
                        if first_token_at is None:
                            first_token_at = now_ms()
                        yield token
                    if chunk.get("done"):
                        break
        except httpx.RequestError as exc:
            raise OllamaConnectionError(f"Ollama request failed: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            detail = _read_error_body(exc.response)
            raise OllamaConnectionError(
                f"Ollama returned {exc.response.status_code}: {detail}"
            ) from exc

        self.last_ttft_ms = (first_token_at - start) if first_token_at else 0.0
        self.last_total_ms = elapsed_ms(start)

    def chat(self, prompt: str) -> dict[str, Any]:
        """Non-streaming chat; returns response text and metrics."""
        start = now_ms()
        url = f"{self.base_url}/api/chat"

        try:
            resp = self._client.post(url, json=self._chat_payload(prompt, stream=False))
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError as exc:
            raise OllamaConnectionError(f"Ollama request failed: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaConnectionError(
                f"Ollama returned {exc.response.status_code}: {_read_error_body(exc.response)}"
            ) from exc

        message = data.get("message", {})
        response_text = message.get("content", "")
        total_latency = elapsed_ms(start)

        eval_count = data.get("eval_count")
        prompt_eval_count = data.get("prompt_eval_count", 0)
        token_count = (
            eval_count
            if eval_count is not None
            else count_tokens_approx(response_text)
        )

        eval_duration_ns = data.get("eval_duration", 0) or 0
        load_duration_ns = data.get("load_duration", 0) or 0
        ttft = (load_duration_ns / 1_000_000) if load_duration_ns else total_latency * 0.1

        duration_sec = max(eval_duration_ns / 1e9, total_latency / 1000, 0.001)
        tps = round(token_count / duration_sec, 2) if token_count else 0.0

        return {
            "response": response_text,
            "tokens_per_sec": tps,
            "ttft": round(ttft, 2),
            "total_latency": round(total_latency, 2),
            "token_count": token_count + (prompt_eval_count or 0),
        }

    def close(self) -> None:
        self._client.close()
