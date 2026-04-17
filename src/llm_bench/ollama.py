"""Ollama API client with streaming metrics collection."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import httpx

OLLAMA_DEFAULT_URL = "http://localhost:11434"


@dataclass
class RunMetrics:
    model: str
    prompt_name: str
    tokens_generated: int
    eval_duration_s: float
    tokens_per_second: float
    ttft_s: float
    load_duration_s: float
    prompt_eval_duration_s: float
    total_duration_s: float
    vram_mb: float | None  # populated separately via /api/ps


def generate_streaming(
    prompt: str,
    model: str,
    base_url: str = OLLAMA_DEFAULT_URL,
    timeout: int = 120,
) -> RunMetrics:
    """Run a single generation and return collected metrics."""
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": True}

    ttft_s: float | None = None
    request_start = time.perf_counter()
    final_chunk: dict = {}

    with httpx.Client(timeout=timeout) as client:
        with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                if ttft_s is None and chunk.get("response"):
                    ttft_s = time.perf_counter() - request_start
                if chunk.get("done"):
                    final_chunk = chunk
                    break

    # Ollama reports durations in nanoseconds
    ns = 1_000_000_000
    eval_count: int = final_chunk.get("eval_count", 0)
    eval_duration_ns: int = final_chunk.get("eval_duration", 0)
    load_duration_ns: int = final_chunk.get("load_duration", 0)
    prompt_eval_duration_ns: int = final_chunk.get("prompt_eval_duration", 0)
    total_duration_ns: int = final_chunk.get("total_duration", 0)

    eval_duration_s = eval_duration_ns / ns if eval_duration_ns else 0.0
    tokens_per_second = eval_count / eval_duration_s if eval_duration_s > 0 else 0.0

    # TTFT from wall-clock or from Ollama's own breakdown (whichever is available)
    if ttft_s is None:
        ttft_s = (load_duration_ns + prompt_eval_duration_ns) / ns

    return RunMetrics(
        model=model,
        prompt_name="",
        tokens_generated=eval_count,
        eval_duration_s=eval_duration_s,
        tokens_per_second=tokens_per_second,
        ttft_s=ttft_s,
        load_duration_s=load_duration_ns / ns,
        prompt_eval_duration_s=prompt_eval_duration_ns / ns,
        total_duration_s=total_duration_ns / ns,
        vram_mb=None,
    )


def list_models(base_url: str = OLLAMA_DEFAULT_URL) -> list[str]:
    url = f"{base_url.rstrip('/')}/api/tags"
    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        resp.raise_for_status()
    return [m["name"] for m in resp.json().get("models", [])]


def get_model_vram_mb(model: str, base_url: str = OLLAMA_DEFAULT_URL) -> float | None:
    """Return VRAM usage in MB for the currently loaded model, or None."""
    url = f"{base_url.rstrip('/')}/api/ps"
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(url)
            resp.raise_for_status()
        for entry in resp.json().get("models", []):
            if entry.get("name", "").split(":")[0] == model.split(":")[0]:
                size_vram = entry.get("size_vram", 0)
                return size_vram / (1024 * 1024) if size_vram else None
    except Exception:
        pass
    return None
