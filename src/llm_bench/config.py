"""Config file loading for llm-bench."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


DEFAULT_CONFIG = """\
# llm-bench configuration file

# Ollama API base URL
host = "http://localhost:11434"

# Models to benchmark
models = ["mistral", "llama3", "phi3"]

# Prompts used for each benchmark run
[[prompts]]
name = "short"
text = "What is the capital of France?"

[[prompts]]
name = "reasoning"
text = "Explain the difference between a list and a tuple in Python."

[[prompts]]
name = "creative"
text = "Write a haiku about programming."

# How many times to repeat each model+prompt pair (results are averaged)
runs_per_pair = 3

# Request timeout in seconds
timeout = 120
"""


@dataclass
class PromptConfig:
    name: str
    text: str


@dataclass
class BenchConfig:
    host: str = "http://localhost:11434"
    models: list[str] = field(default_factory=lambda: ["mistral"])
    prompts: list[PromptConfig] = field(default_factory=list)
    runs_per_pair: int = 3
    timeout: int = 120

    @classmethod
    def from_path(cls, path: Path) -> BenchConfig:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        prompts = [PromptConfig(name=p["name"], text=p["text"]) for p in raw.get("prompts", [])]
        return cls(
            host=raw.get("host", "http://localhost:11434"),
            models=raw.get("models", ["mistral"]),
            prompts=prompts or [PromptConfig(name="default", text="What is 2+2?")],
            runs_per_pair=raw.get("runs_per_pair", 3),
            timeout=raw.get("timeout", 120),
        )

    @classmethod
    def default(cls) -> BenchConfig:
        return cls(
            prompts=[
                PromptConfig(name="short", text="What is the capital of France?"),
                PromptConfig(
                    name="reasoning",
                    text="Explain the difference between a list and a tuple in Python.",
                ),
                PromptConfig(name="creative", text="Write a haiku about programming."),
            ]
        )
