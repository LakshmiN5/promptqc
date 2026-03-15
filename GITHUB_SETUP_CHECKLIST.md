# GitHub Repository Setup Checklist

Complete these tasks in the GitHub web UI to finish the v0.2.0 release preparation.

## 1. Repository About Section

**Location:** Go to https://github.com/LakshmiN5/promptqc → Click the gear icon ⚙️ next to "About" on the right sidebar

### Add Description
```
ESLint for your system prompts — catch contradictions, anti-patterns, injection vulnerabilities, and token waste before production
```

### Add Website
```
https://pypi.org/project/promptqc/
```

### Add Topics (Tags)
Add these topics for better discoverability:
- `prompt-engineering`
- `llm`
- `static-analysis`
- `developer-tools`
- `ai-security`
- `linter`
- `quality-assurance`
- `prompt-injection`
- `gpt`
- `claude`
- `python`
- `ci-cd`

## 2. Enable GitHub Discussions

**Location:** Settings → Features → Discussions

1. Go to https://github.com/LakshmiN5/promptqc/settings
2. Scroll down to "Features" section
3. Check the box next to "Discussions"
4. Click "Set up discussions"
5. GitHub will create a welcome discussion automatically

### Suggested Discussion Categories
- 💡 Ideas (for feature requests)
- 🙏 Q&A (for questions)
- 📣 Show and tell (for sharing prompts that PromptQC helped improve)
- 💬 General (for everything else)

## 3. Create GitHub Release

**Location:** https://github.com/LakshmiN5/promptqc/releases/new

### Release Details
- **Tag:** `v0.2.0` (already pushed)
- **Release title:** `v0.2.0 - LLM Judge, Auto-Fix, Enhanced Security`
- **Description:** Copy content from `RELEASE_NOTES_v0.2.0.md`

### Steps:
1. Go to https://github.com/LakshmiN5/promptqc/releases/new
2. Select tag: `v0.2.0`
3. Set release title: `v0.2.0 - LLM Judge, Auto-Fix, Enhanced Security`
4. Copy the entire content from `RELEASE_NOTES_v0.2.0.md` into the description
5. Check "Set as the latest release"
6. Click "Publish release"

## 4. Optional: Add Terminal GIF/Screenshot

To make the README more compelling, record a terminal demo:

### Using asciinema (recommended)
```bash
# Install asciinema
brew install asciinema  # macOS
# or: pip install asciinema

# Record a demo
asciinema rec demo.cast

# During recording, run:
promptqc check test_prompts/bad_prompt.txt

# Stop recording with Ctrl+D

# Upload to asciinema
asciinema upload demo.cast

# Add the embed link to README.md
```

### Using terminalizer (alternative)
```bash
npm install -g terminalizer

# Record
terminalizer record demo

# Render as GIF
terminalizer render demo

# Upload the GIF to GitHub and add to README
```

### Where to add in README
Replace the TODO comment at line 27 in README.md with:
```markdown
![PromptQC Demo](https://asciinema.org/a/YOUR_RECORDING_ID.svg)
```

## 5. Verify Everything

After completing the above:

- [ ] Repository has description, website, and topics
- [ ] Discussions tab is visible and enabled
- [ ] Release v0.2.0 is published with full release notes
- [ ] README badges show correct discussion/issue counts
- [ ] SECURITY.md is visible in the repository
- [ ] Optional: Terminal demo is added to README

## 6. Announce the Release

Consider announcing on:
- Twitter/X with hashtags: #PromptEngineering #LLM #AI
- Reddit: r/MachineLearning, r/LanguageTechnology
- Hacker News: Show HN
- LinkedIn
- Dev.to or Medium blog post

---

**All code changes are complete and committed. These are UI-only tasks that must be done manually in GitHub.**