# PromptQC v0.2.0 - LLM Judge, Auto-Fix, Enhanced Security

**ESLint for your system prompts** — catch contradictions, anti-patterns, injection vulnerabilities, and token waste before they reach production.

## 🎯 Highlights

This release focuses on **accuracy improvements** and **advanced analysis capabilities**:

- ✅ **83.3% Accuracy** - Improved from 66.7% through stricter scoring and better detection
- 🤖 **LLM Judge Mode** - Deep semantic analysis using any LLM provider (Groq, Ollama, OpenAI, Anthropic, 100+ more)
- 🔧 **Auto-Fix** - Automatically correct common issues (filler phrases, negative framing)
- 🔒 **Enhanced Security** - 100% detection of critical vulnerabilities
- 🎨 **Better UX** - Cleaner output, configuration files, inline rule disabling

## 🚀 What's New

### LLM Judge Mode
Deep semantic analysis using any LLM via LiteLLM:
```bash
# Use Groq (fast & free)
promptqc check prompt.txt --judge groq/llama3-8b-8192

# Use local Ollama
promptqc check prompt.txt --judge ollama/phi3

# Use OpenAI
promptqc check prompt.txt --judge gpt-4o-mini
```

Detects subtle issues:
- Tone consistency problems
- Deep semantic contradictions
- Hallucination risk patterns

### Auto-Fix Mode
Automatically correct deterministic issues:
```bash
promptqc check prompt.txt --fix
```

Fixes:
- Removes filler phrases ("in order to" → "to")
- Converts negative framing to positive instructions
- Safely writes improvements back to your file

### Enhanced Security Detection
5 new critical security patterns:
- Direct code execution without validation
- Shell command execution
- SQL injection via string concatenation
- Trusting all user input
- Disabling input sanitization

### Configuration File Support
Create `promptqc.toml` for project-level settings:
```bash
promptqc init
```

Configure:
- Disable specific rules globally
- Set default token model
- Configure LLM judge model
- Customize thresholds

### Inline Rule Disabling
Suppress specific rules with comments:
```python
# promptqc-disable-next-line PQ003
"Do not hallucinate"

# promptqc-disable-line PQ005
"In order to provide the best service..."
```

## 📊 Improvements

### Stricter Scoring
Calibrated deduction amounts for better accuracy:
- ERROR: 15 → 20 points
- WARNING: 8 → 12 points
- SUGGESTION: 3 → 5 points
- **Result: 83.3% accuracy** (up from 66.7%)

### Better Detection
- Contradiction detection now catches "Be brief, but include all details"
- Security issues now correctly score 0/F instead of 94/A
- Vague prompts now score D instead of B
- Template variable detection improved for multi-line XML tags

### Cleaner Output
- Suppressed verbose LiteLLM logs
- Only shows errors when needed
- Better formatted results

## 🔧 Breaking Changes

None! All v0.1.0 code continues to work.

## 📦 Installation

```bash
# Upgrade to v0.2.0
pip install --upgrade promptqc

# Optional: Install LLM judge support
pip install promptqc[llm]

# Optional: Install semantic analysis
pip install promptqc[semantic]

# Install everything
pip install promptqc[all]
```

## 🐛 Bug Fixes

- Fixed Python 3.14 compatibility by removing spaCy dependency
- Fixed contradiction detection for intra-sentence conflicts
- Fixed security scoring to properly penalize critical issues
- Fixed vague prompt scoring to be more accurate

## 📚 Documentation

- Added SECURITY.md with vulnerability reporting guidelines
- Updated README with better structure and examples
- Added GitHub Discussions and Issues badges
- Reframed "Known Limitations" as "What's Coming"
- Updated roadmap to reflect shipped features

## 🙏 Thank You

Thank you to everyone who provided feedback and helped improve PromptQC!

## 🔗 Links

- [PyPI Package](https://pypi.org/project/promptqc/)
- [GitHub Repository](https://github.com/LakshmiN5/promptqc)
- [Documentation](https://github.com/LakshmiN5/promptqc#readme)
- [Report Issues](https://github.com/LakshmiN5/promptqc/issues)
- [Discussions](https://github.com/LakshmiN5/promptqc/discussions)

---

**Full Changelog**: https://github.com/LakshmiN5/promptqc/blob/main/CHANGELOG.md