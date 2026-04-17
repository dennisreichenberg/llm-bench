# llm-bench

A lightweight CLI tool for benchmarking local LLMs via [Ollama](https://ollama.ai).  
Compare models on the metrics that matter: **tokens/s**, **time-to-first-token (TTFT)**, and **VRAM usage**.

---

## Features

- Benchmark any models available in your local Ollama installation
- Configure models, prompts, and run counts via a TOML config file
- Measures: **tokens/s**, **TTFT**, **total duration**, **VRAM (MB)**
- Averages results over multiple runs to reduce noise
- Export results as **JSON**, **CSV**, or **Markdown table**
- Minimal dependencies: `click`, `httpx`, `rich`

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) running locally (default: `http://localhost:11434`)

---

## Installation

```bash
pip install llm-bench
```

Or from source:

```bash
git clone https://github.com/dennisreichenberg/llm-bench
cd llm-bench
pip install -e .
```

---

## Quick Start

```bash
# List available models
llm-bench models

# Run with defaults (3 prompts × 3 runs per pair)
llm-bench --models mistral,llama3

# Run from a config file and save results as Markdown
llm-bench --config bench.toml --output results.md

# Export as JSON
llm-bench --models phi3 --output results.json --runs 5
```

---

## Example Output

```
llm-bench — benchmarking 2 model(s) × 3 prompt(s) × 3 run(s)
Ollama: http://localhost:11434

┏━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Model   ┃ Prompt    ┃ Runs ┃ Tokens/s  ┃ TTFT (s) ┃ Total (s) ┃ Avg Tokens ┃ VRAM (MB) ┃
┡━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ mistral │ short     │    3 │      48.2 │    0.121 │      1.84 │         89 │      4096 │
│ mistral │ reasoning │    3 │      46.7 │    0.118 │      4.31 │        202 │      4096 │
│ mistral │ creative  │    3 │      49.1 │    0.122 │      0.98 │         48 │      4096 │
│ llama3  │ short     │    3 │      38.4 │    0.243 │      2.12 │         81 │      5120 │
│ llama3  │ reasoning │    3 │      37.9 │    0.238 │      5.04 │        191 │      5120 │
│ llama3  │ creative  │    3 │      39.1 │    0.241 │      1.13 │         44 │      5120 │
└─────────┴───────────┴──────┴───────────┴──────────┴───────────┴────────────┴───────────┘
```

---

## Configuration File

Generate a default config:

```bash
llm-bench init
# Creates bench.toml in the current directory
```

Example `bench.toml`:

```toml
host = "http://localhost:11434"
models = ["mistral", "llama3", "phi3"]
runs_per_pair = 3
timeout = 120

[[prompts]]
name = "short"
text = "What is the capital of France?"

[[prompts]]
name = "reasoning"
text = "Explain the difference between a list and a tuple in Python."

[[prompts]]
name = "creative"
text = "Write a haiku about programming."
```

---

## Metrics Explained

| Metric | Description |
|---|---|
| **Tokens/s** | Generation speed: `eval_count / eval_duration` reported by Ollama |
| **TTFT (s)** | Time-to-first-token: wall-clock time from request sent to first response byte |
| **Total (s)** | Total wall time including model loading and prompt evaluation |
| **VRAM (MB)** | GPU memory used by the model, sampled after first run via `/api/ps` |

> **Note:** VRAM is only reported when Ollama has a GPU backend and the model is loaded. It shows `—` otherwise.

---

## CLI Reference

```
Usage: llm-bench [OPTIONS] COMMAND [ARGS]...

  Benchmark local LLMs via Ollama.

Options:
  -c, --config PATH           Path to TOML config file.
  --host TEXT                 Ollama base URL (overrides config).
  -m, --models TEXT           Comma-separated list of models.
  -n, --runs INTEGER          Runs per model/prompt pair.
  -o, --output PATH           Output file path.
  --format [json|csv|markdown]  Output format.
  --help                      Show this message and exit.

Commands:
  init    Generate a default bench.toml config file.
  models  List available Ollama models.
```

---

## License

MIT — see [LICENSE](LICENSE).
