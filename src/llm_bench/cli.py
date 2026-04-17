"""CLI entry point for llm-bench."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.table import Table

from .benchmark import AggregatedResult, run_benchmark
from .config import DEFAULT_CONFIG, BenchConfig
from .export import to_csv, to_json, to_markdown

console = Console()
err = Console(stderr=True)


def _build_results_table(results: list[AggregatedResult]) -> Table:
    table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
    table.add_column("Model", style="bold white")
    table.add_column("Prompt", style="dim")
    table.add_column("Runs", justify="right")
    table.add_column("Tokens/s", justify="right", style="green")
    table.add_column("TTFT (s)", justify="right")
    table.add_column("Total (s)", justify="right")
    table.add_column("Avg Tokens", justify="right")
    table.add_column("VRAM (MB)", justify="right")

    for r in results:
        table.add_row(
            r.model,
            r.prompt_name,
            str(r.runs),
            f"{r.avg_tokens_per_second:.1f}",
            f"{r.avg_ttft_s:.3f}",
            f"{r.avg_total_duration_s:.2f}",
            f"{r.avg_tokens_generated:.0f}",
            f"{r.vram_mb:.0f}" if r.vram_mb is not None else "-",
        )
    return table


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--config", "-c", "config_path", default=None, type=click.Path(), help="Path to TOML config file.")
@click.option("--host", default=None, help="Ollama base URL (overrides config).")
@click.option("--models", "-m", default=None, help="Comma-separated list of models to benchmark.")
@click.option("--runs", "-n", default=None, type=int, help="Runs per model/prompt pair.")
@click.option("--output", "-o", default=None, type=click.Path(), help="Output file path (auto-detects format from extension).")
@click.option("--format", "fmt", default=None, type=click.Choice(["json", "csv", "markdown"]), help="Output format (overrides extension detection).")
def main(
    ctx: click.Context,
    config_path: str | None,
    host: str | None,
    models: str | None,
    runs: int | None,
    output: str | None,
    fmt: str | None,
) -> None:
    """Benchmark local LLMs via Ollama.

    Measures tokens/s, time-to-first-token, and VRAM usage across models.

    \b
    Examples:
      llm-bench
      llm-bench --models mistral,llama3 --runs 2
      llm-bench --config bench.toml --output results.json
      llm-bench --output results.md --format markdown
    """
    if ctx.invoked_subcommand is not None:
        return

    # Load config
    if config_path:
        cfg = BenchConfig.from_path(Path(config_path))
    else:
        cfg = BenchConfig.default()

    # CLI overrides
    if host:
        cfg.host = host
    if models:
        cfg.models = [m.strip() for m in models.split(",")]
    if runs is not None:
        cfg.runs_per_pair = runs

    console.print(f"[bold]llm-bench[/bold] — benchmarking [cyan]{len(cfg.models)}[/cyan] model(s) × [cyan]{len(cfg.prompts)}[/cyan] prompt(s) × [cyan]{cfg.runs_per_pair}[/cyan] run(s)")
    console.print(f"[dim]Ollama: {cfg.host}[/dim]\n")

    results: list[AggregatedResult] = []

    def on_progress(model, prompt, run_idx, total_runs):
        console.print(f"  [dim]{model}[/dim] · [dim]{prompt.name}[/dim] · run {run_idx}/{total_runs}…", end="\r")

    try:
        results = run_benchmark(cfg, progress_callback=on_progress)
    except httpx.ConnectError:
        err.print(f"\n[red]Cannot connect to Ollama at {cfg.host}.[/red] Is Ollama running?")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        err.print(f"\n[red]Ollama API error {exc.response.status_code}:[/red] {exc.response.text[:200]}")
        sys.exit(1)

    console.print()
    if not results:
        err.print("[yellow]No results collected.[/yellow] Check your model names and Ollama connection.")
        sys.exit(1)

    console.print(_build_results_table(results))

    # Export if requested
    out_path = Path(output) if output else None
    resolved_fmt = fmt
    if out_path and not resolved_fmt:
        suffix = out_path.suffix.lstrip(".")
        if suffix in {"json", "csv", "md", "markdown"}:
            resolved_fmt = "markdown" if suffix in {"md", "markdown"} else suffix

    if resolved_fmt == "json":
        to_json(results, out_path)
        if out_path:
            console.print(f"\n[dim]Saved JSON → {out_path}[/dim]")
        else:
            console.print(to_json(results))
    elif resolved_fmt == "csv":
        to_csv(results, out_path)
        if out_path:
            console.print(f"\n[dim]Saved CSV → {out_path}[/dim]")
        else:
            console.print(to_csv(results))
    elif resolved_fmt == "markdown":
        to_markdown(results, out_path)
        if out_path:
            console.print(f"\n[dim]Saved Markdown → {out_path}[/dim]")
        else:
            console.print(to_markdown(results))


@main.command("init")
@click.option("--output", "-o", default="bench.toml", show_default=True, help="Where to write the config file.")
@click.option("--force", is_flag=True, help="Overwrite existing file.")
def init_cmd(output: str, force: bool) -> None:
    """Generate a default llm-bench.toml config file."""
    path = Path(output)
    if path.exists() and not force:
        err.print(f"[yellow]{path} already exists.[/yellow] Use --force to overwrite.")
        sys.exit(1)
    path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    console.print(f"[green]Created[/green] {path} — edit it, then run: [bold]llm-bench --config {path}[/bold]")


@main.command("models")
@click.option("--host", default="http://localhost:11434", show_default=True, help="Ollama base URL.")
def models_cmd(host: str) -> None:
    """List available Ollama models."""
    from .ollama import list_models
    try:
        available = list_models(host)
    except httpx.ConnectError:
        err.print(f"[red]Cannot connect to Ollama at {host}.[/red]")
        sys.exit(1)

    if not available:
        console.print("[yellow]No models found.[/yellow] Pull one with: ollama pull mistral")
        return

    console.print("[bold]Available Ollama models:[/bold]")
    for m in available:
        console.print(f"  [cyan]{m}[/cyan]")
