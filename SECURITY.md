# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **lakshmi.sunil5486@gmail.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Considerations for PromptQC Users

### Prompt Injection Detection

PromptQC is designed to **detect** prompt injection vulnerabilities in system prompts, but it does not provide runtime protection. When using PromptQC:

1. **Review all findings**: Pay special attention to PQ006 (overly permissive instructions) and PQ007 (missing anti-extraction defenses)
2. **Test in isolation**: Always test prompts in a sandboxed environment before production deployment
3. **Use sandboxing**: Implement proper variable sandboxing (see PQ013) for user inputs in multi-line XML tags

### LLM Judge Mode Security

When using `--judge` mode with external LLM APIs:

- **API Keys**: Never commit API keys to version control. Use environment variables.
- **Prompt Content**: Be aware that your prompt content is sent to the LLM provider for analysis.
- **Local Alternative**: Use `--judge ollama/model-name` for fully local analysis if prompt content is sensitive.

### CI/CD Integration

When integrating PromptQC into CI/CD pipelines:

- Use `--fast` mode to avoid downloading ML models in CI environments
- Store API keys in GitHub Secrets or equivalent secure storage
- Review JSON output programmatically to enforce quality gates

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

## Comments on This Policy

If you have suggestions on how this process could be improved, please submit a pull request or open an issue.

---

**Thank you for helping keep PromptQC and its users safe!** 🔒