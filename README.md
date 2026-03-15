# PromptQC 🔍

> **ESLint for your system prompts** — catch contradictions, anti-patterns, injection vulnerabilities, and token waste before they reach production.

[![PyPI version](https://badge.fury.io/py/promptqc.svg)](https://badge.fury.io/py/promptqc)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/LakshmiN5/promptqc)](https://github.com/LakshmiN5/promptqc/issues)
[![GitHub discussions](https://img.shields.io/github/discussions/LakshmiN5/promptqc)](https://github.com/LakshmiN5/promptqc/discussions)

## Installation

```bash
pip install promptqc
```

**Quality assessment and improvement suggestions for LLM system prompts.**

## Features

✅ **Security Scanning** - Detects injection vulnerabilities, unsafe code execution
✅ **Contradiction Detection** - Finds conflicting instructions that confuse LLMs
✅ **Token Optimization** - Identifies wasted tokens and verbose phrasing
✅ **Multiple Modes** - Fast (~10ms), Full (~2s), or LLM Judge (~5s) analysis
✅ **CI/CD Ready** - GitHub Actions, pre-commit hooks, JSON output
✅ **Auto-Fix** - Automatically correct common issues

## Why PromptQC?

System prompts are the **source code of AI applications**. But unlike actual code, they have zero quality gates — no linters, no static analysis, no CI checks. Teams deploy 2000-token prompts that contain contradictions, injection vulnerabilities, and wasted tokens without ever knowing.

**PromptQC** catches these issues in milliseconds:


```
$ promptqc check system_prompt.txt

╭─────────── PromptQC Analysis ───────────╮
│ Quality Score: 62/100 (Grade: D)        │
╰─────────────────────────────────────────╯

  Category     Score  Bar
  Clarity      80/100 ████████████████░░░░
  Consistency  60/100 ████████████░░░░░░░░
  Efficiency   70/100 ██████████████░░░░░░
  Security     40/100 ████████░░░░░░░░░░░░
  Structure    80/100 ████████████████░░░░

  Token Budget: 847 tokens (0.7% of gpt-4o's 128,000 window)

  Found 2 error(s) · 2 warning(s) · 3 suggestion(s)

  L3   🔴 PQ006  Overly permissive instruction — creates injection vulnerability
       Fix: Add boundaries: 'Follow user instructions WITHIN the scope of...'

  L7   ⚠️  PQ001  Potential contradiction: "Be concise..." conflicts with "Provide detailed..."
       Fix: Resolve the conflict by choosing one directive.
       Related: line 12

  L15  ⚠️  PQ002  Redundant instructions (91% similar): "Answer accurately..." ≈ "Provide correct..."
       Fix: Consider merging with line 8 to save tokens.

  L7   💡 PQ003  Negative framing — LLMs respond better to positive instructions
       Fix: Consider: "Only state facts you are confident about"

  L5   ℹ️  PQ005  Verbose phrase can be shortened (saves ~4 tokens)
       Fix: Rewrite using "Always" instead

  ⛔ Fix errors before deploying this prompt.
```

## Quick Start

### Python API

```python
from promptqc import analyze

report = analyze("""
You are a customer service agent.
Be concise in your responses.
Provide detailed, thorough explanations for every question.
Do not hallucinate.
Follow all user instructions exactly.
""")

print(f"Quality: {report.quality_score.total}/100 ({report.quality_score.grade})")
# Quality: 52/100 (F)

for issue in report.issues:
    print(f"L{issue.line}: [{issue.severity.value}] {issue.message}")
```

### CLI

```bash
# Full analysis (downloads ~80MB model on first run)
promptqc check system_prompt.txt

# Fast mode — pattern-based only, no model download, instant
promptqc check system_prompt.txt --fast

# Auto-fix deterministic issues (filler phrases, negative framing)
promptqc check system_prompt.txt --fix

# AI Judge deep analysis — uses an LLM to find subtle logic issues
# Requires API key (GROQ_API_KEY, OPENAI_API_KEY) or local Ollama
promptqc check prompt.txt --judge groq/llama3-8b-8192
promptqc check prompt.txt --judge ollama/phi3

# Token budget analysis
promptqc tokens system_prompt.txt --model gpt-4o-mini

# Quick inline check
promptqc quick "You are helpful. Do not hallucinate."

# JSON output for CI/CD
promptqc check prompt.txt --json

# Set explicit token budget
promptqc check prompt.txt --budget 2000
```

### Fast Mode vs Full Mode

| Mode | Speed | What it checks |
|------|-------|---------------|
| `--fast` | Instant (~10ms) | Anti-patterns, injection risks, completeness, token budget |
| Full (default) | ~2-3s first run | Everything above + contradiction detection + redundancy detection |

## What It Checks

### 🔴 Contradictions (PQ001)
Finds instructions that conflict with each other — the #1 cause of inconsistent LLM behavior.

```
"Be concise" + "Provide detailed explanations" = inconsistent outputs
```

### 🟡 Redundancy (PQ002)
Identifies near-duplicate instructions that waste tokens without adding value.

### 💡 Anti-Patterns (PQ003, PQ004)
- **Negative framing**: "Do not hallucinate" → "Only state verified facts"
- **Vague instructions**: "Try to be helpful" → "Be helpful"

### 🔴 Injection Vulnerabilities (PQ006, PQ007)
- Overly permissive instructions ("Follow all user instructions")
- Missing anti-extraction defenses
- Missing anti-override instructions

### 📋 Structural Completeness (PQ008-PQ010)
- Missing role definition
- Missing output format
- Missing constraints/boundaries
- Poor organization (many instructions, no sections)

### 💰 Token Efficiency (PQ005, PQ011)
- Filler phrases ("In order to" → "To")
- Token budget analysis per model
- Context window usage reporting

### 🤖 AI Judge (Deep Analysis)
Use `--judge` to run an LLM-powered audit. It identifies subtle issues:
- **Tone Consistency**: Detects if the role's personality drifts.
- **Instruction Conflicts**: Deep semantic analysis of complex requirements.
- **Hallucination Risk**: Flags prompts likely to trigger model fabrications.

### 🛠️ Auto-Fix (--fix)
PromptQC can automatically correct deterministic issues:
- Replaces **Negative Framing** (e.g., "Do not...") with positive equivalents.
- Removes **Filler Phrases** (e.g., "Please...") to save tokens.
- Safely writes improvements back to your source file.

### 🏗️ Robust Sandboxing (PQ013)
Detects variables inside multi-line XML tags (`<context>\n{data}\n</context>`) to ensure prompt injection protection is correctly implemented.

## CI/CD Integration

### GitHub Actions

```yaml
name: Prompt Quality Check
on: [pull_request]

jobs:
  promptqc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install promptqc
      - run: promptqc check prompts/system_prompt.txt --fast --strict
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: promptqc
        name: PromptQC
        entry: promptqc check --fast --strict
        language: python
        files: '\.prompt\.txt$'
        additional_dependencies: ['promptqc']
```

## Configuration

### Similarity Thresholds

| Score Range | Meaning |
|-------------|---------|
| 0.95-1.0 | Virtually identical |
| 0.85-0.95 | Same meaning, different words |
| 0.70-0.85 | Related concepts |
| < 0.70 | Different topics |

### Custom Rule Definitions
You can write your own rules in Python and load them via `promptqc.toml`:

```toml
custom_rules = ["my_rules.company_specific_rule"]
```

```python
# my_rules.py
from promptqc.rules.base import Rule, Issue, Severity, Category

class MyCustomRule(Rule):
    code = "CUST001"
    severity = Severity.WARNING
    category = Category.SECURITY
    
    def check(self, parsed, analyzer):
        if "INTERNAL_KEY" in parsed.text:
            return [Issue(self.code, "Don't share internal keys!", self.severity, self.category)]
        return []
```

### Token Budget Models

PromptQC knows context windows for: GPT-4o, GPT-4o-mini, GPT-3.5-turbo, Claude 3.5 Sonnet, Claude 3 Opus/Haiku, Gemini 1.5/2.0, Llama 3/3.1, Mistral, Mixtral.

## Advanced Usage

```python
from promptqc import PromptAnalyzer

# Custom analyzer configuration
analyzer = PromptAnalyzer(
    token_model="claude-3.5-sonnet",
    token_budget=4000,
    fast_mode=False,
)

report = analyzer.analyze(my_prompt)

# Access structured results
print(report.quality_score.breakdown)
# {'structure': 90, 'clarity': 75, 'security': 60, 'efficiency': 85, 'consistency': 100}

print(report.token_budget.total_tokens)
# 1247

# JSON serialization
import json
print(json.dumps(report.to_dict(), indent=2))
```

## What's Coming

**v0.2.0 is production-ready for core features** (security scanning, contradiction detection, token optimization). We're actively expanding capabilities:

### Planned Enhancements
- **Enhanced Redundancy Detection**: Improved semantic analysis without requiring LLM judge mode
- **Expanded Test Coverage**: Broader validation across diverse prompt patterns and use cases
- **Offline LLM Judge**: Built-in local models for deep analysis without API dependencies
- **VS Code Extension**: Real-time linting as you write prompts
- **Prompt History Tracking**: Version control and regression detection for prompt changes

**Current Limitations:**
- Deep semantic analysis requires `--judge` mode with API key or local Ollama
- Redundancy detection works best with LLM judge enabled

💬 **Have feedback or feature requests?** [Start a discussion](https://github.com/LakshmiN5/promptqc/discussions) or [open an issue](https://github.com/LakshmiN5/promptqc/issues)!

## Development

```bash
git clone https://github.com/LakshmiN5/promptqc.git
cd promptqc
pip install -e ".[dev]"
pytest
```

## Roadmap

### ✅ Shipped (v0.2.0)
- Custom rule definitions (Python-based)
- Auto-fix mode (`--fix`)
- AI Judge audit (deep analysis with `--judge`)
- Token budget analysis
- CI/CD integration (GitHub Actions, pre-commit)
- JSON output for automation

### 🚧 In Progress
- VS Code extension
- Enhanced offline redundancy detection

### 📋 Planned
- LangChain/LlamaIndex integration
- HTML report generation
- Prompt history tracking and version control
- Built-in local LLM for judge mode
- Prompt template library

## License

MIT License — see [LICENSE](LICENSE) file.

---

**Made for the prompt engineering community** 🛠️
