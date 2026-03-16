# Changelog

All notable changes to PromptQC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-03-16

### Added
- **MiniMax Provider Support**: Added MiniMax as a first-class LLM judge provider
  - 204K context window for analyzing large system prompts
  - OpenAI-compatible API integration via LiteLLM
  - Auto-configuration for `minimax/` prefix
  - Usage: `promptqc check prompt.txt --judge minimax/MiniMax-M2.5`
  - Requires `MINIMAX_API_KEY` environment variable

## [0.2.0] - 2026-03-14

### Added
- **LLM Judge Mode**: Deep semantic analysis using any LLM via LiteLLM
  - Support for Groq, Ollama, OpenAI, Anthropic, and 100+ providers
  - Detects subtle contradictions and semantic issues
  - Usage: `promptqc check prompt.txt --judge groq/llama3-8b-8192`
- **Auto-Fix Mode**: Automatically fix deterministic issues
  - Removes filler phrases (e.g., "in order to" → "to")
  - Converts negative framing to positive instructions
  - Usage: `promptqc check prompt.txt --fix`
- **Enhanced Security Detection**: 5 new critical security patterns
  - Direct code execution without validation
  - Shell command execution
  - SQL injection via string concatenation
  - Trusting all user input
  - Disabling input sanitization
- **Vagueness Detection**: New rule PQ011 for extremely vague prompts
  - Detects prompts <50 words with <5 instructions
  - WARNING severity
- **Template Variable Sandboxing**: Detects unsafe variable usage
  - Checks for XML tag sandboxing (`<context>{var}</context>`)
  - Prevents prompt injection vulnerabilities
- **Configuration File Support**: `promptqc.toml` for project-level settings
  - Disable specific rules globally
  - Set default token model
  - Configure LLM judge model
  - Customize thresholds
  - Usage: `promptqc init` to create config file
- **Inline Rule Disabling**: Suppress specific rules with comments
  - `# promptqc-disable-next-line PQ003`
  - `# promptqc-disable-line PQ005`

### Changed
- **Stricter Scoring**: Calibrated deduction amounts for better accuracy
  - ERROR: 15 → 20 points
  - WARNING: 8 → 12 points
  - SUGGESTION: 3 → 5 points
  - Result: 83.3% accuracy (up from 66.7%)
- **Improved Contradiction Detection**: Enhanced LLM judge prompts
  - Better detection of intra-sentence contradictions
  - More precise semantic conflict analysis
- **Suppressed LiteLLM Logs**: Cleaner console output
  - No more verbose provider information
  - Only shows errors when needed

### Removed
- **spaCy Dependency**: Removed for better compatibility
  - Fixes Python 3.14 compatibility issues
  - Simpler installation
  - Faster dependency resolution

### Fixed
- Contradiction detection now catches "Be brief, but include all details"
- Security issues now correctly score 0/F instead of 94/A
- Vague prompts now score D instead of B
- Template variable detection improved for multi-line XML tags

## [0.1.0] - 2026-03-01

### Added
- Initial release of PromptQC
- **Core Analysis Engine**
  - Pattern-based rule checking
  - Semantic similarity analysis using sentence-transformers
  - Token counting for 15+ models (GPT, Claude, Gemini, Llama, etc.)
- **Quality Scoring System**
  - Overall score (0-100) with letter grades (A-F)
  - Category breakdown (structure, clarity, security, efficiency, consistency)
- **Rule Categories**
  - PQ001: Contradiction detection
  - PQ002: Redundancy detection
  - PQ003: Negative framing anti-pattern
  - PQ004: Vague instructions
  - PQ005: Filler phrases (token waste)
  - PQ006: Injection vulnerabilities
  - PQ007: Missing anti-extraction defenses
  - PQ008: Missing role definition
  - PQ009: Missing output format
  - PQ010: Missing constraints
  - PQ011: Token budget analysis
  - PQ012: Poor organization
- **CLI Interface**
  - `promptqc check` - Analyze a prompt file
  - `promptqc quick` - Quick inline analysis
  - `promptqc tokens` - Token usage breakdown
  - `--fast` mode for instant pattern-based checks
  - `--json` output for CI/CD integration
  - `--strict` mode for errors/warnings only
- **Python API**
  - `analyze()` - Full analysis
  - `analyze_fast()` - Fast mode
  - `PromptAnalyzer` class for custom configuration
- **CI/CD Integration**
  - GitHub Actions example
  - Pre-commit hook example
  - JSON output for automation
- **Documentation**
  - Comprehensive README with examples
  - Rule explanations and fix suggestions
  - Token model reference
  - CI/CD integration guides

### Known Limitations
- Redundancy detection doesn't catch verbose synonym lists (25% accuracy)
- Requires manual threshold tuning for some edge cases

---

## Release Notes

### v0.2.0 Highlights

This release focuses on **accuracy improvements** and **advanced analysis capabilities**:

1. **83.3% Accuracy**: Improved from 66.7% through stricter scoring and better detection
2. **LLM Judge**: Deep semantic analysis using any LLM provider
3. **Auto-Fix**: Automatically correct common issues
4. **Enhanced Security**: 100% detection of critical vulnerabilities
5. **Better UX**: Cleaner output, configuration files, inline rule disabling

### Upgrade Guide

```bash
# Upgrade to v0.2.0
pip install --upgrade promptqc

# Optional: Install LLM judge support
pip install promptqc[llm]

# Create config file (optional)
promptqc init
```

No breaking changes - all v0.1.0 code continues to work.

---

## Future Roadmap

### v0.3.0 (Planned)
- [ ] Improved redundancy detection (pattern-based)
- [ ] Configurable severity levels per rule
- [ ] HTML report generation
- [ ] Prompt history tracking
- [ ] VS Code extension (beta)

### v1.0.0 (Target: 90%+ Accuracy)
- [ ] Advanced redundancy detection (90%+ accuracy)
- [ ] Multi-language prompt support
- [ ] Prompt optimization suggestions
- [ ] Team collaboration features
- [ ] Enterprise integrations (LangChain, LlamaIndex)

---

**For detailed changes, see the [commit history](https://github.com/LakshmiN5/promptqc/commits/main).**