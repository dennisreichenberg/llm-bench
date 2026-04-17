"""Tests for the export module."""

import json

from llm_bench.benchmark import AggregatedResult
from llm_bench.export import to_csv, to_json, to_markdown


def _make_result(**kwargs) -> AggregatedResult:
    defaults = dict(
        model="mistral",
        prompt_name="short",
        runs=3,
        avg_tokens_per_second=42.5,
        avg_ttft_s=0.123,
        avg_total_duration_s=2.5,
        avg_tokens_generated=80.0,
        vram_mb=1024.0,
        raw=[],
    )
    defaults.update(kwargs)
    return AggregatedResult(**defaults)


def test_to_json_roundtrip():
    results = [_make_result(), _make_result(model="llama3", vram_mb=None)]
    text = to_json(results)
    parsed = json.loads(text)
    assert len(parsed) == 2
    assert parsed[0]["model"] == "mistral"
    assert parsed[1]["vram_mb"] is None


def test_to_csv_headers():
    results = [_make_result()]
    text = to_csv(results)
    first_line = text.splitlines()[0]
    assert "model" in first_line
    assert "tokens_per_second" in first_line


def test_to_markdown_table():
    results = [_make_result()]
    text = to_markdown(results)
    assert "|" in text
    assert "mistral" in text
    assert "42.5" in text


def test_to_markdown_no_vram():
    results = [_make_result(vram_mb=None)]
    text = to_markdown(results)
    assert "| - |" in text or "|-|" in text or "| - " in text
