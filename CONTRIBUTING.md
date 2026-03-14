# Contributing to PromptQC

Thank you for your interest in contributing to PromptQC! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/LakshmiN5/promptqc/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, PromptQC version)
   - Sample prompt that triggers the issue (if applicable)

### Suggesting Features

1. Check existing [Issues](https://github.com/LakshmiN5/promptqc/issues) for similar suggestions
2. Create a new issue with:
   - Clear use case description
   - Why this feature would be valuable
   - Proposed implementation (optional)

### Contributing Code

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/LakshmiN5/promptqc.git
cd promptqc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

#### Development Workflow

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Write clear, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests and linting**:
   ```bash
   pytest
   black src/ tests/
   ruff check src/ tests/
   ```
5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request** on GitHub

#### Pull Request Guidelines

- **Title**: Clear, descriptive title following conventional commits
- **Description**: Explain what changes you made and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update README.md or other docs if needed
- **Single Purpose**: One feature/fix per PR
- **Small PRs**: Easier to review and merge

### Adding Custom Rules

PromptQC is designed to be extensible. You can add custom rules:

```python
# my_custom_rule.py
from promptqc.rules.base import BaseRule
from promptqc.models import Issue, Severity

class MyCustomRule(BaseRule):
    rule_id = "CUSTOM001"
    name = "my-custom-rule"
    category = "custom"
    description = "Checks for my specific pattern"
    
    def check(self, parsed, analyzer):
        issues = []
        if "bad_pattern" in parsed.raw_text:
            issues.append(Issue(
                rule_id=self.rule_id,
                severity=Severity.WARNING,
                message="Found bad pattern",
                line=1,
                line_content=parsed.get_line_text(1),
                category=self.category,
            ))
        return issues
```

To contribute a rule to the main repository:
1. Add it to `src/promptqc/rules/`
2. Register it in `src/promptqc/rules/__init__.py`
3. Add tests in `tests/`
4. Add test prompts in `test_suite/`
5. Document it in README.md

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/promptqc --cov-report=html

# Run specific test file
pytest tests/test_promptqc.py

# Run specific test
pytest tests/test_promptqc.py::test_contradiction_detection
```

#### Writing Tests

```python
def test_my_feature():
    """Test description."""
    from promptqc import analyze
    
    prompt = "Your test prompt here"
    report = analyze(prompt)
    
    assert report.quality_score.total >= 80
    assert len(report.issues) == 0
```

#### Test Suite

Add test prompts to `test_suite/`:
- `good_prompts/` - High-quality prompts (should score A/B)
- `bad_prompts/` - Low-quality prompts (should score D/F)
- `edge_cases/` - Edge cases and stress tests

Run the accuracy test suite:
```bash
cd test_suite
python3 run_accuracy_test.py
```

### Code Style

- **Python**: Follow PEP 8
- **Line Length**: 100 characters (configured in pyproject.toml)
- **Formatting**: Use `black` for automatic formatting
- **Linting**: Use `ruff` for linting
- **Type Hints**: Use type hints where appropriate
- **Docstrings**: Use Google-style docstrings

Example:
```python
def analyze_prompt(prompt: str, fast_mode: bool = False) -> Report:
    """
    Analyze a prompt for quality issues.
    
    Args:
        prompt: The system prompt text to analyze
        fast_mode: If True, skip semantic analysis
        
    Returns:
        Report with issues, token budget, and quality score
        
    Raises:
        ValueError: If prompt is empty
    """
    pass
```

### Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Update CHANGELOG.md (see below)

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. Build and publish to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Questions?

- Open an [Issue](https://github.com/LakshmiN5/promptqc/issues)
- Start a [Discussion](https://github.com/LakshmiN5/promptqc/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PromptQC! 🚀