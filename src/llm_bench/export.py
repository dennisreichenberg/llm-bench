"""Export benchmark results to JSON, CSV, or Markdown."""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from .benchmark import AggregatedResult

_FIELDS = [
    "model",
    "prompt",
    "runs",
    "tokens_per_second",
    "ttft_s",
    "total_duration_s",
    "avg_tokens_generated",
    "vram_mb",
]


def _to_rows(results: list[AggregatedResult]) -> list[dict]:
    rows = []
    for r in results:
        rows.append(
            {
                "model": r.model,
                "prompt": r.prompt_name,
                "runs": r.runs,
                "tokens_per_second": round(r.avg_tokens_per_second, 2),
                "ttft_s": round(r.avg_ttft_s, 3),
                "total_duration_s": round(r.avg_total_duration_s, 3),
                "avg_tokens_generated": round(r.avg_tokens_generated, 1),
                "vram_mb": round(r.vram_mb, 0) if r.vram_mb is not None else None,
            }
        )
    return rows


def to_json(results: list[AggregatedResult], path: Path | None = None) -> str:
    payload = _to_rows(results)
    text = json.dumps(payload, indent=2)
    if path:
        path.write_text(text, encoding="utf-8")
    return text


def to_csv(results: list[AggregatedResult], path: Path | None = None) -> str:
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=_FIELDS)
    writer.writeheader()
    writer.writerows(_to_rows(results))
    text = buf.getvalue()
    if path:
        path.write_text(text, encoding="utf-8")
    return text


def to_markdown(results: list[AggregatedResult], path: Path | None = None) -> str:
    rows = _to_rows(results)
    headers = ["Model", "Prompt", "Runs", "Tokens/s", "TTFT (s)", "Total (s)", "Avg Tokens", "VRAM (MB)"]
    col_keys = _FIELDS

    def fmt(v) -> str:
        return "-" if v is None else str(v)

    lines: list[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        cols = [fmt(row[k]) for k in col_keys]
        lines.append("| " + " | ".join(cols) + " |")

    text = "\n".join(lines) + "\n"
    if path:
        path.write_text(text, encoding="utf-8")
    return text
