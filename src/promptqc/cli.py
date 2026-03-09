"""Command-line interface for promptqc."""

import sys
import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from promptqc.models import Severity, Report


console = Console()


def _format_report(report: Report, show_suggestions: bool = True) -> None:
    """Render a report to the terminal using Rich."""
    score = report.quality_score
    budget = report.token_budget
    counts = report.summary_counts()

    # ── Header ──
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}
    grade_color = grade_colors.get(score.grade, "white")

    header = Text()
    header.append("Quality Score: ", style="bold")
    header.append(f"{score.total}/100 ", style=f"bold {grade_color}")
    header.append(f"(Grade: {score.grade})", style=grade_color)

    console.print(Panel(header, title="[bold cyan]PromptQC Analysis[/bold cyan]", border_style="cyan"))

    # ── Score breakdown ──
    if score.breakdown:
        score_table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        score_table.add_column("Category", style="cyan")
        score_table.add_column("Score", justify="right")
        score_table.add_column("Bar", min_width=20)

        for cat, val in sorted(score.breakdown.items()):
            bar_len = val // 5  # 0-20 chars
            bar_color = "green" if val >= 80 else ("yellow" if val >= 60 else "red")
            bar = f"[{bar_color}]{'█' * bar_len}{'░' * (20 - bar_len)}[/{bar_color}]"
            score_table.add_row(cat.capitalize(), f"{val}/100", bar)

        console.print(score_table)

    # ── Token budget ──
    if budget:
        usage_color = "green"
        if budget.usage_percent > 25:
            usage_color = "yellow"
        if budget.usage_percent > 50:
            usage_color = "red"

        budget_text = (
            f"[bold]{budget.total_tokens:,}[/bold] tokens "
            f"([{usage_color}]{budget.usage_percent:.1f}%[/{usage_color}] of "
            f"{budget.model_name}'s {budget.context_window:,} context window) · "
            f"[green]{budget.tokens_remaining:,}[/green] remaining"
        )
        console.print(Panel(budget_text, title="[bold]Token Budget[/bold]", border_style="dim"))

        # Section breakdown
        if budget.section_tokens and len(budget.section_tokens) > 1:
            sec_table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
            sec_table.add_column("Section", style="dim")
            sec_table.add_column("Tokens", justify="right", style="dim")
            for name, toks in sorted(budget.section_tokens.items(), key=lambda x: -x[1]):
                sec_table.add_row(name, f"{toks:,}")
            console.print(sec_table)

    # ── Issues ──
    if not report.issues:
        console.print("\n[bold green]✅ No issues found! Your prompt looks great.[/bold green]\n")
        return

    # Summary line
    parts = []
    if counts["errors"]:
        parts.append(f"[red]{counts['errors']} error(s)[/red]")
    if counts["warnings"]:
        parts.append(f"[yellow]{counts['warnings']} warning(s)[/yellow]")
    if counts["suggestions"]:
        parts.append(f"[blue]{counts['suggestions']} suggestion(s)[/blue]")
    if counts["info"]:
        parts.append(f"[dim]{counts['info']} info[/dim]")
    console.print(f"\nFound {' · '.join(parts)}\n")

    # Issue details
    severity_styles = {
        Severity.ERROR: ("🔴", "red"),
        Severity.WARNING: ("⚠️ ", "yellow"),
        Severity.SUGGESTION: ("💡", "blue"),
        Severity.INFO: ("ℹ️ ", "dim"),
    }

    for issue in report.issues:
        if not show_suggestions and issue.severity in (Severity.SUGGESTION, Severity.INFO):
            continue

        icon, color = severity_styles.get(issue.severity, ("?", "white"))

        console.print(f"  [{color}]L{issue.line:>3}[/{color}]  {icon} [{color}]{issue.rule_id}[/{color}]  {issue.message}")

        if issue.suggestion:
            console.print(f"        [dim]Fix: {issue.suggestion}[/dim]")

        if issue.related_line:
            console.print(f"        [dim]Related: line {issue.related_line}[/dim]")

        console.print()

    # ── Exit guidance ──
    if counts["errors"] > 0:
        console.print("[red bold]⛔ Fix errors before deploying this prompt.[/red bold]")
    elif counts["warnings"] > 0:
        console.print("[yellow]⚠️  Review warnings — they likely affect prompt behavior.[/yellow]")
    else:
        console.print("[green]✅ No critical issues. Suggestions are optional improvements.[/green]")


@click.group()
@click.version_option(version="0.1.0", prog_name="promptqc")
def main():
    """
    PromptQC — Quality assessment for LLM system prompts.

    Analyzes prompts for contradictions, redundancy, anti-patterns,
    injection vulnerabilities, and token efficiency.
    """
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--model", "-m", default="gpt-4o", help="Model for token counting (default: gpt-4o)")
@click.option("--budget", "-b", type=int, help="Maximum token budget for the prompt")
@click.option("--fast", is_flag=True, help="Skip semantic analysis (no model download, instant)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--strict", is_flag=True, help="Show only errors and warnings")
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
def check(file, model, budget, fast, output_json, strict, output):
    """
    Analyze a prompt file for quality issues.

    Examples:

        promptqc check system_prompt.txt

        promptqc check prompt.txt --model gpt-4o-mini --budget 2000

        promptqc check prompt.txt --fast --json
    """
    prompt_text = Path(file).read_text(encoding="utf-8")

    if not fast:
        console.print("[dim]Loading semantic analysis model...[/dim]", highlight=False)

    from promptqc import analyze, analyze_fast, PromptAnalyzer

    if fast:
        report = analyze_fast(prompt_text, token_model=model, token_budget=budget)
    else:
        report = analyze(prompt_text, token_model=model, token_budget=budget)

    if output_json:
        result = json.dumps(report.to_dict(), indent=2)
        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]✓ Report saved to {output}[/green]")
        else:
            click.echo(result)
    else:
        _format_report(report, show_suggestions=not strict)
        if output:
            # Save plain text version
            Path(output).write_text(
                json.dumps(report.to_dict(), indent=2),
                encoding="utf-8",
            )
            console.print(f"\n[green]✓ JSON report saved to {output}[/green]")

    # Exit code: 1 if errors, 0 otherwise
    if report.errors:
        sys.exit(1)


@main.command()
@click.argument("text")
@click.option("--model", "-m", default="gpt-4o", help="Model for token counting")
def quick(text, model):
    """
    Quick analysis of a prompt string (fast mode, no semantic analysis).

    Example:

        promptqc quick "You are a helpful assistant. Do not hallucinate."
    """
    from promptqc import analyze_fast
    report = analyze_fast(text, token_model=model)
    _format_report(report)

    if report.errors:
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--model", "-m", default="gpt-4o", help="Model for token counting")
def tokens(file, model):
    """
    Show token usage breakdown for a prompt file.

    Example:

        promptqc tokens system_prompt.txt --model gpt-4o-mini
    """
    from promptqc.parser import parse_prompt
    from promptqc.rules.tokens import compute_token_budget, MODEL_CONTEXT_WINDOWS

    prompt_text = Path(file).read_text(encoding="utf-8")
    parsed = parse_prompt(prompt_text)

    # Show for requested model
    budget = compute_token_budget(parsed, model)

    console.print(Panel(
        f"[bold]{budget.total_tokens:,}[/bold] tokens for [cyan]{model}[/cyan]",
        title="[bold]Token Count[/bold]",
        border_style="cyan",
    ))

    # Section breakdown
    if budget.section_tokens:
        table = Table(title="Section Breakdown", box=box.ROUNDED)
        table.add_column("Section", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("% of Total", justify="right")

        for name, toks in sorted(budget.section_tokens.items(), key=lambda x: -x[1]):
            pct = (toks / budget.total_tokens * 100) if budget.total_tokens > 0 else 0
            table.add_row(name, f"{toks:,}", f"{pct:.1f}%")

        console.print(table)

    # Multi-model comparison
    console.print("\n[bold]Context Window Usage Across Models:[/bold]")
    compare_table = Table(box=box.SIMPLE)
    compare_table.add_column("Model", style="cyan")
    compare_table.add_column("Context Window", justify="right")
    compare_table.add_column("Usage", justify="right")
    compare_table.add_column("Remaining", justify="right")

    for m_name, ctx_size in sorted(MODEL_CONTEXT_WINDOWS.items(), key=lambda x: x[1]):
        pct = (budget.total_tokens / ctx_size) * 100
        remaining = ctx_size - budget.total_tokens
        color = "green" if pct < 10 else ("yellow" if pct < 25 else "red")
        compare_table.add_row(
            m_name,
            f"{ctx_size:,}",
            f"[{color}]{pct:.2f}%[/{color}]",
            f"{remaining:,}",
        )

    console.print(compare_table)


if __name__ == "__main__":
    main()
