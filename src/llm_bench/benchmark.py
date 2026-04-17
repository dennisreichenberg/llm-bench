"""Benchmark runner: iterates models × prompts × runs and aggregates results."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from .config import BenchConfig, PromptConfig
from .ollama import RunMetrics, generate_streaming, get_model_vram_mb


@dataclass
class AggregatedResult:
    model: str
    prompt_name: str
    runs: int
    avg_tokens_per_second: float
    avg_ttft_s: float
    avg_total_duration_s: float
    avg_tokens_generated: float
    vram_mb: float | None
    raw: list[RunMetrics] = field(default_factory=list)


def run_benchmark(
    config: BenchConfig,
    progress_callback=None,
) -> list[AggregatedResult]:
    """Run the full benchmark suite and return aggregated results."""
    results: list[AggregatedResult] = []

    for model in config.models:
        for prompt in config.prompts:
            raw_runs: list[RunMetrics] = []
            vram_mb: float | None = None

            for run_idx in range(config.runs_per_pair):
                if progress_callback:
                    progress_callback(model, prompt, run_idx + 1, config.runs_per_pair)
                try:
                    metrics = generate_streaming(
                        prompt=prompt.text,
                        model=model,
                        base_url=config.host,
                        timeout=config.timeout,
                    )
                    metrics.prompt_name = prompt.name
                    raw_runs.append(metrics)

                    # Sample VRAM after the first run (model should be loaded)
                    if run_idx == 0 and vram_mb is None:
                        vram_mb = get_model_vram_mb(model, config.host)

                except httpx.ConnectError:
                    raise
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        # Model not found — skip remaining runs for this model
                        break
                    raise

            if not raw_runs:
                continue

            results.append(
                AggregatedResult(
                    model=model,
                    prompt_name=prompt.name,
                    runs=len(raw_runs),
                    avg_tokens_per_second=_mean(r.tokens_per_second for r in raw_runs),
                    avg_ttft_s=_mean(r.ttft_s for r in raw_runs),
                    avg_total_duration_s=_mean(r.total_duration_s for r in raw_runs),
                    avg_tokens_generated=_mean(r.tokens_generated for r in raw_runs),
                    vram_mb=vram_mb,
                    raw=raw_runs,
                )
            )

    return results


def _mean(values) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0
