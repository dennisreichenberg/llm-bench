"""Tests for config loading."""

import textwrap
from pathlib import Path

import pytest

from llm_bench.config import BenchConfig


def test_default_config():
    cfg = BenchConfig.default()
    assert "http://localhost:11434" in cfg.host
    assert len(cfg.prompts) >= 1
    assert cfg.runs_per_pair >= 1


def test_from_toml(tmp_path: Path):
    toml = textwrap.dedent("""
        host = "http://custom:11434"
        models = ["phi3", "gemma"]
        runs_per_pair = 2
        timeout = 60

        [[prompts]]
        name = "greeting"
        text = "Say hello."
    """)
    p = tmp_path / "bench.toml"
    p.write_text(toml, encoding="utf-8")
    cfg = BenchConfig.from_path(p)
    assert cfg.host == "http://custom:11434"
    assert cfg.models == ["phi3", "gemma"]
    assert cfg.runs_per_pair == 2
    assert cfg.prompts[0].name == "greeting"
